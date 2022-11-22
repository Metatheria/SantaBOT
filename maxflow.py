"""Module implementing a maxflow algorithm

https://en.wikipedia.org/wiki/Maximum_flow_problem"""

import math


def find_next_node(graph, source, sink, forbidden):
    for i in range(len(graph[source])):
        if graph[source][i] > 0 and i not in forbidden:
            path = find_path(graph, i, sink, forbidden)
            if path is not None:
                return i, path
    return None, None


def find_path(graph, source, sink, forbidden):
    if graph[source][sink] > 0:
        return [source, sink]
    else:
        next_node, path = find_next_node(graph, source, sink, forbidden + [source])
        if next_node:
            return [source] + path
        else:
            return None

def min_flow(graph, path):
    flow = math.inf
    for i in range(len(path)-1):
        flow = min(flow, graph[path[i]][path[i+1]])
    return flow

def add_path_flow(graph, path, flow):
    for i in range(len(path)-1):
        graph[path[i]][path[i+1]] -= flow
        graph[path[i+1]][path[i]] += flow

def maxflow(graph,source,sink):
    path = find_path(graph,source,sink,[])
    total_flow = 0
    while path is not None:
        flow = min_flow(graph, path)
        """
        print("Path:")
        print(path)
        print("Min flow:")
        print(flow)
        """
        add_path_flow(graph, path, flow)
        total_flow += flow
        path = find_path(graph,source,sink,[])
    """
    print("Total flow:")
    print(total_flow)
    """
    return total_flow

