# -*- coding: utf-8 -*-

import enum
import itertools
import json
import random
import typing as t


class Step(t.TypedDict):
    step: int
    robots: list[int]
    robotCount: list[int]
    nodeStatus: list[str]
    traversed: list[bool]


class Graph(t.TypedDict):
    n: int
    edges: list[list[int]]
    adjacencyList: list[list[int]]


class Result(t.TypedDict):
    tree: Graph
    steps: list[Step]


class NodeStatus(enum.Enum):
    """
    Three exclusive cases for each node v in which some robots are currently located
    (denote by T_v the subtree rooted at node v):
        - FINISHED
            - all edges in T_v are visited by at least one robot
            and there is no robot in T_v or all robots are located at node v
        - UNFINISHED
            - some edges in T_v are not visited by any robot
        - INHABITED
            - all edges in T_v are visited by at least one robot,
            but some robots are in T_u for some child node u of v

    Note: based on the assumption that the tree is unknown, these states are not
    determined until the vertex is visited. For example, the parent node of a leaf
    does not yet know that the leaf itself is in the finished state.
    """

    FINISHED = "FINISHED"
    UNFINISHED = "UNFINISHED"
    INHABITED = "INHABITED"


def collective_tree_exploration(k: int, tree: list[list[int]], root: int):
    """
    params:
        k: number of robots
        tree: directed graph provided by adjacency list
        r: root of the tree
    """

    n: t.Final[int] = len(tree)

    parents: t.Final[list[int]] = [-1] * n
    edges: t.Final[list[tuple[int, int]]] = [
        (v, u) for v, adj in enumerate(tree) for u in adj
    ]
    for v, u in edges:
        parents[u] = v

    # traversed[v] := whether node v is traversed by any robot (for visualization)
    traversed: t.Final[list[bool]] = [False] * n
    traversed[root] = True

    # robots[i] := node at which robot i is located
    robots: list[int] = [root] * k

    # robot_count[v] := number of robots at node v
    robot_count: list[int] = [0] * n
    robot_count[root] = k

    # robot_count_in_subtree[v] := number of robots in the subtree rooted at node v
    robot_count_in_subtree: list[int] = [0] * n
    robot_count_in_subtree[root] = k

    # node_status[v] := status of node v
    node_status: list[NodeStatus] = [NodeStatus.UNFINISHED] * n

    yield 0, robots, robot_count, node_status, traversed.copy()

    for step in itertools.count(1):
        next_robots: list[int] = [-1] * k

        for v, robots_indices in convert_to_indices_mapping(robots):
            if node_status[v] == NodeStatus.FINISHED:
                for i in robots_indices:
                    next_robots[i] = root if v == root else parents[v]

            elif node_status[v] == NodeStatus.UNFINISHED:
                us = [u for u in tree[v] if node_status[u] == NodeStatus.UNFINISHED]
                if not us:
                    continue

                xs = [robot_count_in_subtree[u] for u in us]
                # xs = [x0, ..., x_m-1, x_m, ...,] so that x1 = ... = x_m-1 > x_m = ...

                ixm = 0
                for i in range(len(us) - 1):
                    if xs[i] > xs[i + 1]:
                        ixm = i + 1
                        break

                for i, robot_index in enumerate(robots_indices):
                    u = us[(i + ixm) % len(us)]
                    next_robots[robot_index] = u
                    traversed[u] = True

            elif node_status[v] == NodeStatus.INHABITED:
                for i in robots_indices:
                    next_robots[i] = v

        robots = next_robots

        robot_count = [0] * n
        for v in robots:
            robot_count[v] += 1
        robot_count_in_subtree = [0] * n

        for v, u in reversed(edges):
            robot_count_in_subtree[u] += robot_count[u]
            robot_count_in_subtree[v] += robot_count_in_subtree[u]

        next_node_status: list[NodeStatus] = [NodeStatus.UNFINISHED] * n

        for v, u in reversed(edges):
            if len(tree[u]) == 0:
                if node_status[u] == NodeStatus.FINISHED or robot_count[u] > 0:
                    next_node_status[u] = NodeStatus.FINISHED
                else:
                    next_node_status[u] = NodeStatus.UNFINISHED
                continue

            if all(
                next_node_status[w] == NodeStatus.FINISHED
                and robot_count_in_subtree[w] == 0
                for w in tree[u]
            ):
                next_node_status[u] = NodeStatus.FINISHED
            elif all(
                next_node_status[w] in (NodeStatus.FINISHED, NodeStatus.INHABITED)
                for w in tree[u]
            ):
                next_node_status[u] = NodeStatus.INHABITED
            else:
                next_node_status[u] = NodeStatus.UNFINISHED
        else:
            if all(
                node_status[u] == NodeStatus.FINISHED and robot_count_in_subtree[u] == 0
                for u in tree[root]
            ):
                next_node_status[root] = NodeStatus.FINISHED
            elif all(
                node_status[u] in (NodeStatus.FINISHED, NodeStatus.INHABITED)
                for u in tree[root]
            ):
                next_node_status[root] = NodeStatus.INHABITED
            else:
                next_node_status[root] = NodeStatus.UNFINISHED

        node_status = next_node_status

        yield step, robots, robot_count, node_status, traversed.copy()

        if all(node_status[v] == NodeStatus.FINISHED for v in range(n)):
            break


def convert_to_indices_mapping(
    sequence: t.Sequence[int],
) -> t.Generator[tuple[int, list[int]], None, None]:
    """
    Return an iterator of (element, indices) pairs for the given sequence.
    >>> list(convert_to_indices_mapping([1, 2, 3, 1, 2, 3]))
    [(1, [0, 3]), (2, [1, 4]), (3, [2, 5])]
    >>> list(convert_to_indices_mapping([3, 3, 2, 2, 1, 1]))
    [(1, [4, 5]), (2, [2, 3]), (3, [0, 1])
    """

    n: t.Final[int] = len(sequence)

    get = sequence.__getitem__
    for it, grouper in itertools.groupby(sorted(range(n), key=get), key=get):
        yield it, list(grouper)


def graph_to_tree(
    n: int, graph: list[list[int]]
) -> tuple[list[list[int]], list[list[int]]]:
    """
    Return a directed graph like tree and its adjacency list. The tree is
    rooted at the node with the largest degree. Note that node labels is ignored.
    >>> graph_to_tree(5, [[4], [3], [3, 4], [1, 2], [0, 2]])
    ([[0, 1], [0, 2], [1, 3], [2, 4]], [[1, 2], [3], [4], [], []])
    """

    root = max(range(n), key=lambda i: len(graph[i]))

    que: list[int] = [root]
    visited: list[bool] = [False] * n
    tree_edges: list[list[int]] = []

    discovered: list[int] = [root]

    for u in que:
        if visited[u]:
            continue
        visited[u] = True
        for v in graph[u]:
            if visited[v]:
                continue
            discovered.append(v)
            que.append(v)
            tree_edges.append([u, v])

    mapping = {e: i for i, e in enumerate(discovered)}
    tree_edges = [[mapping[u], mapping[v]] for u, v in tree_edges]

    tree: list[list[int]] = [[] for _ in range(n)]
    for u, v in tree_edges:
        tree[u].append(v)

    return tree_edges, tree


def random_tree(n: int, seed: int = 1991) -> list[list[int]]:
    """
    Return a random tree as an adjacency list.
    The tree is generated by a transformation from the Prüfer sequence.
    >>> random_tree(5)
    [[4], [3], [3, 4], [1, 2], [0, 2]]
    >>> random_tree(n=5, seed=0)
    [[3, 4], [3], [3], [1, 2, 0], [0]]
    """

    gen = random.Random(seed)
    seq = [gen.choice(range(n)) for _ in range(n - 2)]

    degree = [1] * n
    for i in seq:
        degree[i] += 1

    graph: list[list[int]] = [[] for _ in range(n)]

    for i in seq:
        for j in range(n):
            if degree[j] == 1:
                graph[i].append(j)
                graph[j].append(i)
                degree[i] -= 1
                degree[j] -= 1
                break

    u, v = {i for i in range(n) if degree[i] == 1}
    graph[u].append(v)
    graph[v].append(u)

    return graph


def run(n: int, k: int, seed: int):
    tree_graph = random_tree(n, seed=seed)
    edges, tree = graph_to_tree(n, tree_graph)

    result: Result = {
        "tree": {"n": n, "edges": edges, "adjacencyList": tree},
        "steps": [],
    }

    for (
        step,
        robots,
        robot_count,
        node_status,
        traversed,
    ) in collective_tree_exploration(k, tree, 0):
        result["steps"].append(
            {
                "step": step,
                "robots": robots,
                "robotCount": robot_count,
                "nodeStatus": [s.value for s in node_status],
                "traversed": traversed,
            }
        )

    return json.dumps(result)
