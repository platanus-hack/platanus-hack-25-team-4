import { useEffect, useRef } from 'react';
import * as d3 from 'd3';
import type { GraphData, GraphNode, GraphEdge } from '../../types/observer.types';
import { graphTransformer } from '../../services/graphTransformer';

interface NetworkGraphCanvasProps {
  data: GraphData;
  width: number;
  height: number;
  onNodeClick?: (node: GraphNode) => void;
  onNodeHover?: (node: GraphNode | null) => void;
}

export function NetworkGraphCanvas({
  data,
  width,
  height,
  onNodeClick,
  onNodeHover,
}: NetworkGraphCanvasProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const simulationRef = useRef<d3.Simulation<GraphNode, GraphEdge> | null>(null);

  useEffect(() => {
    if (!svgRef.current || !data.nodes.length) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove(); // Clear previous render

    // Create container group for zoom/pan
    const container = svg.append('g').attr('class', 'graph-container');

    // Set up zoom behavior
    const zoom = d3
      .zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.1, 4])
      .on('zoom', (event) => {
        container.attr('transform', event.transform);
      });

    svg.call(zoom);

    // Create force simulation
    const simulation = d3
      .forceSimulation<GraphNode>(data.nodes)
      .force(
        'link',
        d3
          .forceLink<GraphNode, GraphEdge>(data.edges)
          .id((d) => d.id)
          .distance(100)
          .strength((d) => d.strength)
      )
      .force('charge', d3.forceManyBody().strength(-300))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(25));

    simulationRef.current = simulation;

    // Create arrow markers for directed edges
    const defs = container.append('defs');

    const categories = ['location', 'collision', 'mission', 'agent_match', 'match', 'conversation', 'chat'];
    categories.forEach((category) => {
      defs
        .append('marker')
        .attr('id', `arrow-${category}`)
        .attr('viewBox', '0 -5 10 10')
        .attr('refX', 20)
        .attr('refY', 0)
        .attr('markerWidth', 6)
        .attr('markerHeight', 6)
        .attr('orient', 'auto')
        .append('path')
        .attr('d', 'M0,-5L10,0L0,5')
        .attr('fill', graphTransformer.getCategoryColor(category as any));
    });

    // Create edges
    const link = container
      .append('g')
      .attr('class', 'links')
      .selectAll('line')
      .data(data.edges)
      .enter()
      .append('line')
      .attr('stroke', (d) => graphTransformer.getCategoryColor(d.type))
      .attr('stroke-width', (d) => Math.min(1 + d.eventCount * 0.5, 5))
      .attr('stroke-opacity', 0.6)
      .attr('marker-end', (d) => `url(#arrow-${d.type})`);

    // Create nodes
    const node = container
      .append('g')
      .attr('class', 'nodes')
      .selectAll('circle')
      .data(data.nodes)
      .enter()
      .append('circle')
      .attr('r', (d) => graphTransformer.getNodeRadius(d.eventCount))
      .attr('fill', (d) => graphTransformer.getCategoryColor(d.category))
      .attr('stroke', '#fff')
      .attr('stroke-width', 2)
      .attr('cursor', 'pointer')
      .call(
        d3
          .drag<SVGCircleElement, GraphNode>()
          .on('start', dragStarted)
          .on('drag', dragged)
          .on('end', dragEnded)
      )
      .on('click', (_event, d) => {
        _event.stopPropagation();
        onNodeClick?.(d);
      })
      .on('mouseenter', (_event, d) => {
        onNodeHover?.(d);
      })
      .on('mouseleave', () => {
        onNodeHover?.(null);
      });

    // Create labels
    const label = container
      .append('g')
      .attr('class', 'labels')
      .selectAll('text')
      .data(data.nodes)
      .enter()
      .append('text')
      .attr('text-anchor', 'middle')
      .attr('dy', (d) => graphTransformer.getNodeRadius(d.eventCount) + 15)
      .attr('font-size', '10px')
      .attr('fill', '#374151')
      .attr('pointer-events', 'none')
      .text((d) => d.label);

    // Update positions on each simulation tick
    simulation.on('tick', () => {
      link
        .attr('x1', (d) => (typeof d.source === 'object' ? d.source.x ?? 0 : 0))
        .attr('y1', (d) => (typeof d.source === 'object' ? d.source.y ?? 0 : 0))
        .attr('x2', (d) => (typeof d.target === 'object' ? d.target.x ?? 0 : 0))
        .attr('y2', (d) => (typeof d.target === 'object' ? d.target.y ?? 0 : 0));

      node.attr('cx', (d) => d.x ?? 0).attr('cy', (d) => d.y ?? 0);

      label.attr('x', (d) => d.x ?? 0).attr('y', (d) => d.y ?? 0);
    });

    // Drag functions
    function dragStarted(dragEvent: d3.D3DragEvent<SVGCircleElement, GraphNode, GraphNode>) {
      if (!dragEvent.active && simulationRef.current) {
        simulationRef.current.alphaTarget(0.3).restart();
      }
      dragEvent.subject.fx = dragEvent.subject.x;
      dragEvent.subject.fy = dragEvent.subject.y;
    }

    function dragged(dragEvent: d3.D3DragEvent<SVGCircleElement, GraphNode, GraphNode>) {
      dragEvent.subject.fx = dragEvent.x;
      dragEvent.subject.fy = dragEvent.y;
    }

    function dragEnded(dragEvent: d3.D3DragEvent<SVGCircleElement, GraphNode, GraphNode>) {
      if (!dragEvent.active && simulationRef.current) {
        simulationRef.current.alphaTarget(0);
      }
      dragEvent.subject.fx = null;
      dragEvent.subject.fy = null;
    }

    // Cleanup
    return () => {
      simulation.stop();
    };
  }, [data, width, height, onNodeClick, onNodeHover]);

  return (
    <svg
      ref={svgRef}
      width={width}
      height={height}
      className="border border-gray-200 rounded-lg bg-white"
    />
  );
}
