"""Monte Carlo simulation engine using NumPy vectorized operations.

Simulates individual transactions flowing through the workflow graph
with stochastic execution times, error occurrences, and branching decisions.
"""

from __future__ import annotations

import numpy as np
from numpy.random import Generator

from prosim.graph.models import NodeType, WorkflowGraph
from prosim.graph.operations import build_nx_graph
from prosim.simulation.bottleneck import compute_bottleneck_scores
from prosim.simulation.results import (
    NodeMetrics,
    SimulationConfig,
    SimulationResults,
)


def run_monte_carlo(
    workflow: WorkflowGraph,
    config: SimulationConfig,
) -> SimulationResults:
    """Run Monte Carlo simulation with stochastic transaction processing.

    Each transaction is simulated individually through the graph:
    1. Start at start node
    2. At each node, sample execution time from normal distribution
    3. At decision nodes, sample branch based on probabilities
    4. Track error/drop events per transaction
    5. Aggregate results across all transactions
    """
    rng = np.random.default_rng(config.seed)
    num_tx = config.num_transactions

    # Pre-compute node lookup and adjacency
    node_map = {n.id: n for n in workflow.nodes}
    outgoing_map: dict[str, list] = {}
    for node in workflow.nodes:
        outgoing_map[node.id] = workflow.get_outgoing_edges(node.id)

    # Per-node accumulators
    node_times: dict[str, list[float]] = {n.id: [] for n in workflow.nodes}
    node_costs: dict[str, list[float]] = {n.id: [] for n in workflow.nodes}
    node_visits: dict[str, int] = {n.id: 0 for n in workflow.nodes}
    node_errors: dict[str, int] = {n.id: 0 for n in workflow.nodes}
    node_drops: dict[str, int] = {n.id: 0 for n in workflow.nodes}
    node_retries: dict[str, int] = {n.id: 0 for n in workflow.nodes}

    # Transaction-level results
    tx_times = np.zeros(num_tx, dtype=np.float64)
    tx_costs = np.zeros(num_tx, dtype=np.float64)
    tx_completed = np.zeros(num_tx, dtype=bool)

    start_nodes = workflow.get_start_nodes()
    if not start_nodes:
        return _empty_results(workflow, config)

    start_id = start_nodes[0].id

    # Simulate each transaction
    for i in range(num_tx):
        current_id = start_id
        total_time = 0.0
        total_cost = 0.0
        dropped = False
        max_hops = len(workflow.nodes) * 10  # Safety limit for loops

        hops = 0
        while current_id and hops < max_hops:
            hops += 1
            node = node_map.get(current_id)
            if not node:
                break

            p = node.params
            node_visits[current_id] += 1

            # Sample execution time (truncated normal, min 0)
            if p.exec_time_variance > 0:
                std = p.exec_time_variance ** 0.5
                exec_time = max(0.0, rng.normal(p.exec_time_mean, std))
            else:
                exec_time = p.exec_time_mean

            # Sample queue delay
            if p.queue_delay_variance > 0:
                std_q = p.queue_delay_variance ** 0.5
                queue_time = max(0.0, rng.normal(p.queue_delay_mean, std_q))
            else:
                queue_time = p.queue_delay_mean

            # Apply parallelization
            effective_time = (exec_time + queue_time) / max(p.parallelization_factor, 1)

            # Check for error
            retries_used = 0
            if p.error_rate > 0 and rng.random() < p.error_rate:
                node_errors[current_id] += 1
                # Retry logic
                for retry in range(p.max_retries):
                    retries_used += 1
                    effective_time += p.retry_delay
                    if p.exec_time_variance > 0:
                        effective_time += max(0.0, rng.normal(p.exec_time_mean, std))
                    else:
                        effective_time += p.exec_time_mean
                    if rng.random() >= p.error_rate:
                        break  # Retry succeeded
                node_retries[current_id] += retries_used

            # Check for drop-off
            if p.drop_off_rate > 0 and rng.random() < p.drop_off_rate:
                node_drops[current_id] += 1
                dropped = True

            # Accumulate
            node_times[current_id].append(effective_time)
            node_costs[current_id].append(p.cost_per_transaction * (1 + retries_used))
            total_time += effective_time
            total_cost += p.cost_per_transaction * (1 + retries_used)

            if dropped:
                break

            # End node reached
            if node.node_type == NodeType.END:
                tx_completed[i] = True
                break

            # Navigate to next node
            edges = outgoing_map.get(current_id, [])
            if not edges:
                break

            if node.node_type == NodeType.DECISION:
                # Probabilistic branching
                probs = np.array([e.probability for e in edges])
                if probs.sum() > 0:
                    probs = probs / probs.sum()
                    choice = rng.choice(len(edges), p=probs)
                    current_id = edges[choice].target
                else:
                    current_id = edges[0].target
            elif node.node_type == NodeType.PARALLEL_GATEWAY:
                # For parallel gateway, take the max time of all branches
                # Simplified: follow each branch, sum max
                # For now, follow the first edge (parallel handling in deterministic)
                current_id = edges[0].target
            else:
                # Follow the single outgoing edge (or first if multiple)
                current_id = edges[0].target

        tx_times[i] = total_time
        tx_costs[i] = total_cost

    # Aggregate results
    completed_mask = tx_completed
    completed_times = tx_times[completed_mask] if completed_mask.any() else tx_times
    completed_costs = tx_costs[completed_mask] if completed_mask.any() else tx_costs

    avg_total_time = float(np.mean(completed_times)) if len(completed_times) > 0 else 0.0
    avg_total_cost = float(np.mean(completed_costs)) if len(completed_costs) > 0 else 0.0

    # Per-node metrics
    total_time_contrib_sum = 0.0
    node_metrics_list = []
    for node in workflow.nodes:
        nid = node.id
        times = node_times[nid]
        costs = node_costs[nid]

        if times:
            t_arr = np.array(times)
            c_arr = np.array(costs)
            avg_t = float(np.mean(t_arr))
            contrib = avg_t * (node_visits[nid] / max(num_tx, 1))
            total_time_contrib_sum += contrib

            # Utilization estimate
            if node.params.capacity_per_hour and node.params.capacity_per_hour > 0:
                demand = config.volume_per_hour * (node_visits[nid] / max(num_tx, 1))
                utilization = min(demand / (node.params.capacity_per_hour * node.params.parallelization_factor), 1.0)
            else:
                utilization = 0.0

            nm = NodeMetrics(
                node_id=nid,
                node_name=node.name,
                avg_time=avg_t,
                p50_time=float(np.percentile(t_arr, 50)),
                p95_time=float(np.percentile(t_arr, 95)),
                p99_time=float(np.percentile(t_arr, 99)),
                total_time_contribution=contrib,
                avg_cost=float(np.mean(c_arr)),
                total_cost=float(np.sum(c_arr)),
                transactions_processed=node_visits[nid],
                transactions_errored=node_errors[nid],
                transactions_dropped=node_drops[nid],
                transactions_retried=node_retries[nid],
                utilization=utilization,
                queue_time=node.params.queue_delay_mean,
            )
        else:
            nm = NodeMetrics(node_id=nid, node_name=node.name)
        node_metrics_list.append(nm)

    # Bottleneck scores
    compute_bottleneck_scores(node_metrics_list, avg_total_time)

    # Throughput
    throughput = 3600.0 / avg_total_time if avg_total_time > 0 else float("inf")

    return SimulationResults(
        config=config,
        workflow_name=workflow.name,
        total_transactions=num_tx,
        completed_transactions=int(completed_mask.sum()),
        failed_transactions=sum(node_errors.values()),
        dropped_transactions=int((~completed_mask).sum()),
        avg_total_time=avg_total_time,
        p50_total_time=float(np.percentile(completed_times, 50)) if len(completed_times) > 0 else 0.0,
        p95_total_time=float(np.percentile(completed_times, 95)) if len(completed_times) > 0 else 0.0,
        p99_total_time=float(np.percentile(completed_times, 99)) if len(completed_times) > 0 else 0.0,
        min_total_time=float(np.min(completed_times)) if len(completed_times) > 0 else 0.0,
        max_total_time=float(np.max(completed_times)) if len(completed_times) > 0 else 0.0,
        avg_total_cost=avg_total_cost,
        total_cost=float(np.sum(tx_costs)),
        throughput_per_hour=throughput,
        max_throughput_per_hour=throughput,
        node_metrics=node_metrics_list,
    )


def _empty_results(workflow: WorkflowGraph, config: SimulationConfig) -> SimulationResults:
    """Return empty results when simulation cannot run."""
    return SimulationResults(
        config=config,
        workflow_name=workflow.name,
    )
