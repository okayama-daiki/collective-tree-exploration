# -*- coding: utf-8 -*-

import itertools
import json
import random
import typing as t


class Step(t.TypedDict):
    step: int
    nodeCase: list[t.Literal[1, 2, 3]]
    positionOfRobots: list[int]
    robotsInNode: list[list[int]]
    isExplored: list[bool]
    isFinished: list[bool]
    isInhabited: list[bool]
    traversed: list[bool]


class Graph(t.TypedDict):
    n: int
    edges: list[list[int]]
    adjacencyList: list[list[int]]


class Result(t.TypedDict):
    tree: Graph
    steps: list[Step]


def collective_tree_exploration(k: int, tree: list[list[int]], root: int):
    """
    params:
        k: number of robots
        tree: directed graph provided by adjacency list
        r: root of the tree
    """

    n: t.Final[int] = len(tree)

    parents: t.Final[list[int]] = [-1] * n

    # NOTE: edges, leaves, internal_nodes has topological order
    edges: t.Final[list[tuple[int, int]]] = [
        (v, u) for v, adj in enumerate(tree) for u in adj
    ]
    for v, u in edges:
        parents[u] = v

    leaves: t.Final[list[int]] = [v for v, adj in enumerate(tree) if not adj]
    internal_nodes: t.Final[list[int]] = [v for v, adj in enumerate(tree) if adj]

    # traversed[v] := whether node v is traversed by any robot
    traversed: t.Final[list[bool]] = [False] * n
    traversed[root] = True

    # robots[i] := node at which robot i is located
    robots: list[int] = [root] * k

    # robot_count[v] := number of robots at node v
    robot_count: list[int] = [0] * n
    robot_count[root] = k

    # robot_count_in_subtree[v] := number of robots in the subtree T_v
    robot_count_in_subtree: list[int] = [0] * n
    robot_count_in_subtree[root] = k

    # `explored` means every edge of T_u has been traversed by some robot
    is_explored: list[bool] = [False] * n

    # `finished` means it is `explored` and either there are no robots in it,
    # or all robots in it are in u
    is_finished: list[bool] = [False] * n

    # `inhabited` it is explored and either there are no robots in it
    is_inhabited: list[bool] = [False] * n

    # for visualization
    node_case: list[t.Literal[1, 2, 3]] = [2] * n

    yield (
        0,
        robots,
        is_explored.copy(),
        is_finished.copy(),
        is_inhabited.copy(),
        traversed.copy(),
        node_case,
    )

    for step in itertools.count(1):
        next_robots: list[int] = [-1] * k

        for v, robots_indices in convert_to_value_indices_mapping(robots):
            # case 1
            if is_finished[v]:
                for i in robots_indices:
                    next_robots[i] = root if v == root else parents[v]
                continue

            # case 2
            if us := [u for u in tree[v] if not is_finished[u]]:
                # x1 = x2 = ... = x_z = x_{z+1} + 1 = ... = x_j + 1
                x = [robot_count_in_subtree[u] for u in us]
                ixz = x.index(min(x))

                it = iter(robots_indices)
                for i in range(len(us)):
                    u = us[(i + ixz) % len(us)]
                    for _ in range(len(robots_indices) // len(us)):
                        next_robots[next(it)] = u
                        traversed[u] = True
                for i in range(len(robots_indices) % len(us)):
                    u = us[(i + ixz) % len(us)]
                    next_robots[next(it)] = u
                    traversed[u] = True

                continue

            # case 3
            if all(is_finished[u] for u in tree[v]) and any(
                is_inhabited[u] for u in tree[v]
            ):
                for i in robots_indices:
                    next_robots[i] = v
                continue

            raise RuntimeError("unreachable")

        robots = next_robots

        robot_count = [0] * n
        for v in robots:
            robot_count[v] += 1

        robot_count_in_subtree = [0] * n
        for v, u in reversed(edges):
            robot_count_in_subtree[u] += robot_count[u]
            robot_count_in_subtree[v] += robot_count_in_subtree[u]

        for leaf in leaves:
            is_explored[leaf] = is_explored[leaf] or robot_count[leaf] > 0
            is_finished[leaf] = is_finished[leaf] or is_explored[leaf]

        for v in reversed(internal_nodes):
            is_explored[v] = is_explored[v] or all(is_explored[u] for u in tree[v])
            is_finished[v] = is_finished[v] or all(
                is_explored[u] and robot_count_in_subtree[u] == 0 for u in tree[v]
            )

        for v in reversed(range(n)):
            is_inhabited[v] = robot_count_in_subtree[v] > 0

        node_case: list[t.Literal[1, 2, 3]] = [
            1
            if is_finished[v]
            else 2
            if any(not is_finished[u] for u in tree[v])
            else 3
            for v in range(n)
        ]

        yield (
            step,
            robots,
            is_explored.copy(),
            is_finished.copy(),
            is_inhabited.copy(),
            traversed.copy(),
            node_case,
        )

        if all(is_finished):
            break


def convert_to_value_indices_mapping(
    sequence: t.Sequence[int],
) -> t.Generator[tuple[int, list[int]], None, None]:
    """
    Return an iterator of (element, indices) pairs for the given sequence.
    >>> list(convert_to_value_indices_mapping([1, 2, 3, 1, 2, 3]))
    [(1, [0, 3]), (2, [1, 4]), (3, [2, 5])]
    >>> list(convert_to_value_indices_mapping([3, 3, 2, 2, 1, 1]))
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
    rooted at the node with the largest degree.

    NOTE: that node labels is ignored.
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
        is_explored,
        is_finished,
        is_inhabited,
        traversed,
        cases,
    ) in collective_tree_exploration(k, tree, 0):
        robots_in_node: list[list[int]] = [[] for _ in range(n)]
        for i, v in enumerate(robots):
            robots_in_node[v].append(i)

        result["steps"].append(
            {
                "step": step,
                "nodeCase": cases,
                "positionOfRobots": robots,
                "robotsInNode": robots_in_node,
                "isExplored": is_explored,
                "isFinished": is_finished,
                "isInhabited": is_inhabited,
                "traversed": traversed,
            }
        )

    return json.dumps(result)
