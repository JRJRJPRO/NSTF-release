#!/usr/bin/env python
"""Debug script to check video_graph structure"""

import pickle
import sys

def main():
    mem_path = "/data1/rongjiej/NSTF_MODEL/data/memory_graphs/robot/kitchen_03.pkl"
    nstf_path = "/data1/rongjiej/NSTF_MODEL/data/nstf_graphs/robot/kitchen_03_nstf_incremental.pkl"
    
    # Load video graph
    print("=" * 60)
    print("Loading video_graph...")
    with open(mem_path, 'rb') as f:
        video_graph = pickle.load(f)
    
    print(f"video_graph type: {type(video_graph)}")
    print(f"video_graph has text_nodes_by_clip: {hasattr(video_graph, 'text_nodes_by_clip')}")
    
    if hasattr(video_graph, 'text_nodes_by_clip'):
        print(f"Number of clips: {len(video_graph.text_nodes_by_clip)}")
        print(f"Clip IDs: {sorted(video_graph.text_nodes_by_clip.keys())[:10]}...")
        
        # Check clip 1
        clip_id = 1
        if clip_id in video_graph.text_nodes_by_clip:
            node_ids = video_graph.text_nodes_by_clip[clip_id]
            print(f"\nClip {clip_id} has {len(node_ids)} nodes")
            
            contents = []
            for nid in node_ids:
                node = video_graph.nodes.get(nid)
                if node:
                    print(f"  Node {nid}:")
                    print(f"    type: {type(node)}")
                    print(f"    has metadata: {hasattr(node, 'metadata')}")
                    if hasattr(node, 'metadata'):
                        print(f"    metadata type: {type(node.metadata)}")
                        print(f"    metadata keys: {node.metadata.keys() if isinstance(node.metadata, dict) else 'not a dict'}")
                        if isinstance(node.metadata, dict):
                            node_contents = node.metadata.get('contents', [])
                            print(f"    contents count: {len(node_contents)}")
                            if node_contents:
                                print(f"    first content: {str(node_contents[0])[:100]}...")
                            contents.extend(str(c) for c in node_contents)
                else:
                    print(f"  Node {nid}: NOT FOUND")
            
            full_content = ' '.join(contents)
            print(f"\n  Full content length: {len(full_content)}")
            print(f"  Full content preview: {full_content[:200]}...")
    
    # Load NSTF graph
    print("\n" + "=" * 60)
    print("Loading NSTF graph...")
    with open(nstf_path, 'rb') as f:
        nstf_graph = pickle.load(f)
    
    proc_nodes = nstf_graph.get('procedure_nodes', {})
    print(f"Number of procedures: {len(proc_nodes)}")
    
    # Check first procedure with episodic_links
    for proc_id, proc in proc_nodes.items():
        episodic_links = proc.get('episodic_links', [])
        if episodic_links:
            print(f"\n{proc_id}:")
            print(f"  Goal: {proc.get('goal', 'N/A')}")
            print(f"  episodic_links count: {len(episodic_links)}")
            for link in episodic_links[:2]:
                clip_id = link.get('clip_id')
                sim = link.get('similarity', 0)
                preview = link.get('content_preview', '')[:50]
                print(f"    Clip {clip_id} (sim={sim:.2f}): {preview}...")
            break

if __name__ == '__main__':
    main()
