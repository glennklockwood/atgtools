#!/usr/bin/env python3
"""
Helper utility to explore elbencho --strided write patterns.

The script mirrors the offset distribution logic in
source/workers/LocalWorker.cpp when OffsetGenStrided is selected:
  * dataset threads = threads_per_host * number_of_hosts
  * each dataset thread (rank) starts at block_size * rank
  * subsequent offsets advance by block_size * dataset_threads (the stride)
  * work is split round-robin across ranks; ranks < remainder get one extra block

Example:
    python tools/strided_offsets.py \
        --threads 2 \
        --hosts localhost:1611,localhost:1612 \
        --size 80 \
        --block 8
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from typing import List, Sequence


@dataclass(frozen=True)
class RankAssignment:
    host: str
    local_thread: int
    rank: int
    blocks: Sequence[int]
    block_size: int

    @property
    def offsets(self) -> Sequence[tuple[int, int]]:
        """Return (start, end) byte ranges for each assigned block."""
        return [
            (block_id * self.block_size, block_id * self.block_size + self.block_size - 1)
            for block_id in self.blocks
        ]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Print per-host/thread offsets for elbencho --strided runs.")
    parser.add_argument("--threads", type=int, required=True, help="Number of threads per host passed to elbencho.")
    parser.add_argument("--hosts", type=str, required=True, help="Comma-separated host list as passed to --hosts.")
    parser.add_argument("--size", type=int, required=True, help="Total file size in bytes.")
    parser.add_argument("--block", type=int, required=True, help="Block size in bytes.")
    parser.add_argument("--rank-offset", type=int, default=0, help="Optional starting rank offset (default: 0).")
    return parser.parse_args()


def compute_rank_assignments(
    threads_per_host: int,
    hosts: Sequence[str],
    file_size: int,
    block_size: int,
    rank_offset: int = 0,
) -> List[RankAssignment]:
    if threads_per_host < 1:
        raise ValueError("--threads must be >= 1")
    if block_size < 1:
        raise ValueError("--block must be >= 1")
    if file_size < block_size:
        raise ValueError("--size must be >= --block")

    num_hosts = len(hosts)
    if num_hosts == 0:
        raise ValueError("--hosts must contain at least one host")

    total_blocks = file_size // block_size
    if total_blocks == 0:
        raise ValueError("Aggregate usable file size must contain at least one full block.")

    num_dataset_threads = threads_per_host * num_hosts
    stride = block_size * num_dataset_threads

    base_blocks = total_blocks // num_dataset_threads
    remainder = total_blocks % num_dataset_threads

    assignments: List[RankAssignment] = []
    rank = rank_offset

    for host in hosts:
        for local_thread in range(threads_per_host):
            num_blocks_for_rank = base_blocks + (1 if (rank - rank_offset) < remainder else 0)
            block_ids = [rank - rank_offset + i * num_dataset_threads for i in range(num_blocks_for_rank)]
            assignments.append(
                RankAssignment(
                    host=host,
                    local_thread=local_thread,
                    rank=rank,
                    blocks=block_ids,
                    block_size=block_size,
                )
            )
            rank += 1

    return assignments


def format_assignment(assignment: RankAssignment, block_size: int, stride: int) -> str:
    lines = [f"{assignment.host}  thread={assignment.local_thread}  rank={assignment.rank}"]
    if not assignment.blocks:
        lines.append("  (no full blocks assigned)")
        return "\n".join(lines)

    for start, end in assignment.offsets:
        block_id = start // block_size
        lines.append(f"  block {block_id:>4d}: bytes {start:>6d} - {end:>6d}")
    lines.append(f"  stride: {stride} bytes")
    return "\n".join(lines)


def main() -> None:
    parsed_args = parse_args()

    hosts = [host.strip() for host in parsed_args.hosts.split(",") if host.strip()]
    remainder = parsed_args.size % parsed_args.block
    if remainder:
        print(
            f"NOTE: file size {parsed_args.size} is not a multiple of block size {parsed_args.block}. "
            f"Last {remainder} bytes are not represented as full blocks.\n"
        )

    assignments = compute_rank_assignments(
        threads_per_host=parsed_args.threads,
        hosts=hosts,
        file_size=parsed_args.size,
        block_size=parsed_args.block,
        rank_offset=parsed_args.rank_offset,
    )

    stride = parsed_args.block * parsed_args.threads * len(hosts)
    for assignment in assignments:
        print(format_assignment(assignment, parsed_args.block, stride))
        print()


if __name__ == "__main__":
    main()
