"""Deterministic simulation engine using probability-weighted DAG traversal.

Computes expected values by traversing the workflow graph and weighting
each path by its cumulative probability.
"""

from __future__ import annotations

from prosim.graph.models import NodeType, WorkflowGraph
from prosim.graph.operations import build_nx_graph, topological_execution_order
from prosim.simulation.bottleneck import compute_bottleneck_scores
from prosim.simulation.results import (
    BottleneckInfo,
    NodeMetrics,
    SimulationConfig,
    SimulationMode,
    SimulationResults,
)


def run_deterministic(
    workflow: WorkflowGraph,
    config: SimulationConfig,
) -> SimulationResults:
    """Run deterministic simulation computing expected values via DAG traversal.

    For each node, computes:
    - Expected time = exec_time_mean + queue_delay_mean (with retry overhead)
    - Expected cost = cost_per_transaction * visit_probability * (1 + error_rate * max_retries)
    - Visit probability = sum of incoming edge probabilities * parent visit probabilities
    """
    G = build_nx_graph(workflow)
    topo_order = topological_execution_order(workflow)

    # Compute visit probability for each node
    visit_prob: dict[str, float] = {}
    for node_id in topo_order:
        node = workflow.get_node(node_id)
        if not node:
            continue
        if node.node_type == NodeType.START:
            visit_prob[node_id] = 1.0
        else:
            incoming = workflow.get_incoming_edges(node_id)
            prob = 0.0
            for edge in incoming:
                parent_prob = visit_prob.get(edge.source, 0.0)
                prob += parent_prob * edge.probability
            visit_prob[node_id] = prob

    # Compute expected arrival time at each node (cumulative from start)
    arrival_time: dict[str, float] = {}
    node_metrics_map: dict[str, NodeMetrics] = {}

    for node_id in topo_order:
        node = workflow.get_node(node_id)
        if not node:
            continue

        p = node.params
        vp = visit_prob.get(node_id, 0.0)

        # Expected time at this node (including retries)
        retry_factor = 1.0 + p.error_rate * p.max_retries
        node_exec_time = (p.exec_time_mean + p.queue_delay_mean) * retry_factor
        effective_time = node_exec_time / max(p.parallelization_factor, 1)

        # Arrival time = max of all parent (arrival_time + their exec time)
        if node.node_type == NodeType.START:
            arrival_time[node_id] = 0.0
        else:
            incoming = workflow.get_incoming_edges(node_id)
            if incoming:
                # Weighted average of parent completion times
                weighted_sum = 0.0
                weight_sum = 0.0
                for edge in incoming:
                    parent_metrics = node_metrics_map.get(edge.source)
                    if parent_metrics:
                        parent_completion = arrival_time.get(edge.source, 0.0) + parent_metrics.avg_time
                        w = visit_prob.get(edge.source, 0.0) * edge.probability
                        weighted_sum += parent_completion * w
                        weight_sum += w
                arrival_time[node_id] = weighted_sum / max(weight_sum, 1e-10)
            else:
                arrival_time[node_id] = 0.0

        # Cost at this node
        node_cost = p.cost_per_transaction * retry_factor

        # Effective throughput through this node
        effective_drop = 1.0 - p.drop_off_rate
        transactions_at_node = int(config.num_transactions * vp)
        transactions_errored = int(transactions_at_node * p.error_rate)
        transactions_dropped = int(transactions_at_node * p.drop_off_rate)
        transactions_retried = int(transactions_errored * min(p.max_retries, 1))

        # Utilization
        if p.capacity_per_hour and p.capacity_per_hour > 0:
            demand = config.volume_per_hour * vp
            utilization = min(demand / (p.capacity_per_hour * p.parallelization_factor), 1.0)
        else:
            utilization = 0.0

        nm = NodeMetrics(
            node_id=node_id,
            node_name=node.name,
            avg_time=effective_time,
            p50_time=effective_time,
            p95_time=effective_time * 1.3,  # Deterministic estimate
            p99_time=effective_time * 1.6,
            total_time_contribution=effective_time * vp,
            avg_cost=node_cost,
            total_cost=node_cost * transactions_at_node,
            transactions_processed=transactions_at_node,
            transactions_errored=transactions_errored,
            transactions_dropped=transactions_dropped,
            transactions_retried=transactions_retried,
            utilization=utilization,
            queue_time=p.queue_delay_mean,
        )
        node_metrics_map[node_id] = nm

    # Compute aggregate metrics
    node_metrics_list = list(node_metrics_map.values())

    # Total time = expected completion time at end nodes
    end_times = []
    for node in workflow.get_end_nodes():
        if node.id in arrival_time and node.id in node_metrics_map:
            end_times.append(arrival_time[node.id] + node_metrics_map[node.id].avg_time)
    avg_total_time = max(end_times) if end_times else 0.0

    # Total cost = sum of node costs weighted by visit probability
    avg_total_cost = sum(
        nm.avg_cost * visit_prob.get(nm.node_id, 0.0)
        for nm in node_metrics_list
    )

    # Throughput
    if avg_total_time > 0:
        throughput = 3600.0 / avg_total_time
    else:
        throughput = float("inf")

    # Max throughput limited by bottleneck capacity
    max_throughput = throughput
    for nm in node_metrics_list:
        node = workflow.get_node(nm.node_id)
        if node and node.params.capacity_per_hour:
            vp = visit_prob.get(nm.node_id, 0.0)
            if vp > 0:
                node_max = node.params.capacity_per_hour * node.params.parallelization_factor / vp
                max_throughput = min(max_throughput, node_max)

    # Completed vs failed vs dropped
    end_visit_prob = sum(visit_prob.get(n.id, 0.0) for n in workflow.get_end_nodes())
    completed = int(config.num_transactions * end_visit_prob)
    total_dropped = sum(nm.transactions_dropped for nm in node_metrics_list)
    total_errored = sum(nm.transactions_errored for nm in node_metrics_list)

    # Compute bottleneck scores
    compute_bottleneck_scores(node_metrics_list, avg_total_time)

    return SimulationResults(
        config=config,
        workflow_name=workflow.name,
        total_transactions=config.num_transactions,
        completed_transactions=completed,
        failed_transactions=total_errored,
        dropped_transactions=total_dropped,
        avg_total_time=avg_total_time,
        p50_total_time=avg_total_time,
        p95_total_time=avg_total_time * 1.3,
        p99_total_time=avg_total_time * 1.6,
        min_total_time=avg_total_time * 0.7,
        max_total_time=avg_total_time * 2.0,
        avg_total_cost=avg_total_cost,
        total_cost=avg_total_cost * config.num_transactions,
        throughput_per_hour=throughput,
        max_throughput_per_hour=max_throughput,
        node_metrics=node_metrics_list,
    )
