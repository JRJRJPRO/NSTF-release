#!/usr/bin/env python3
"""
Analyze baseline results from robot and web datasets.
Calculates: accuracy (gpt_eval), num_rounds, elapsed_time_sec
"""

import json
import os

def analyze_jsonl(filepath, dataset_name):
    """Analyze a JSONL file and return statistics."""
    results = {
        'total': 0,
        'correct': 0,  # gpt_eval == true
        'total_rounds': 0,
        'total_time': 0,
        'by_video': {},  # group by video_id
        'by_type': {}    # group by type_original
    }
    
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            
            try:
                data = json.loads(line)
                results['total'] += 1
                
                # Accuracy
                if data.get('gpt_eval', False):
                    results['correct'] += 1
                
                # Rounds and time
                results['total_rounds'] += data.get('num_rounds', 0)
                results['total_time'] += data.get('elapsed_time_sec', 0)
                
                # Group by video_id
                video_id = data.get('video_id', 'unknown')
                if video_id not in results['by_video']:
                    results['by_video'][video_id] = {
                        'total': 0, 'correct': 0, 'rounds': 0, 'time': 0
                    }
                results['by_video'][video_id]['total'] += 1
                if data.get('gpt_eval', False):
                    results['by_video'][video_id]['correct'] += 1
                results['by_video'][video_id]['rounds'] += data.get('num_rounds', 0)
                results['by_video'][video_id]['time'] += data.get('elapsed_time_sec', 0)
                
                # Group by type_original
                types = data.get('type_original', [])
                for t in types:
                    if t not in results['by_type']:
                        results['by_type'][t] = {
                            'total': 0, 'correct': 0, 'rounds': 0, 'time': 0
                        }
                    results['by_type'][t]['total'] += 1
                    if data.get('gpt_eval', False):
                        results['by_type'][t]['correct'] += 1
                    results['by_type'][t]['rounds'] += data.get('num_rounds', 0)
                    results['by_type'][t]['time'] += data.get('elapsed_time_sec', 0)
                    
            except json.JSONDecodeError as e:
                print(f"Error parsing line: {e}")
                continue
    
    return results

def print_summary(results, dataset_name):
    """Print summary statistics."""
    total = results['total']
    if total == 0:
        print(f"\n{dataset_name}: No data found")
        return
    
    accuracy = results['correct'] / total * 100
    avg_rounds = results['total_rounds'] / total
    avg_time = results['total_time'] / total
    
    print(f"\n{'='*60}")
    print(f" {dataset_name} Dataset - Baseline Results Summary")
    print(f"{'='*60}")
    print(f"\n📊 Overall Statistics:")
    print(f"   Total Questions: {total}")
    print(f"   Correct Answers: {results['correct']}")
    print(f"   Accuracy: {accuracy:.2f}%")
    print(f"   Average Rounds: {avg_rounds:.2f}")
    print(f"   Average Time: {avg_time:.2f} sec")
    print(f"   Total Time: {results['total_time']:.2f} sec")
    
    # Print by video summary
    print(f"\n📹 By Video (Top 10 by question count):")
    sorted_videos = sorted(results['by_video'].items(), 
                          key=lambda x: x[1]['total'], reverse=True)[:10]
    print(f"   {'Video ID':<20} {'Questions':>10} {'Accuracy':>10} {'Avg Rounds':>12} {'Avg Time':>12}")
    print(f"   {'-'*64}")
    for video_id, stats in sorted_videos:
        v_acc = stats['correct'] / stats['total'] * 100 if stats['total'] > 0 else 0
        v_rounds = stats['rounds'] / stats['total'] if stats['total'] > 0 else 0
        v_time = stats['time'] / stats['total'] if stats['total'] > 0 else 0
        print(f"   {video_id:<20} {stats['total']:>10} {v_acc:>9.1f}% {v_rounds:>12.2f} {v_time:>11.2f}s")
    
    # Print by type summary
    print(f"\n🏷️  By Question Type:")
    print(f"   {'Type':<35} {'Questions':>10} {'Accuracy':>10} {'Avg Rounds':>12} {'Avg Time':>12}")
    print(f"   {'-'*79}")
    sorted_types = sorted(results['by_type'].items(), 
                         key=lambda x: x[1]['total'], reverse=True)
    for type_name, stats in sorted_types:
        t_acc = stats['correct'] / stats['total'] * 100 if stats['total'] > 0 else 0
        t_rounds = stats['rounds'] / stats['total'] if stats['total'] > 0 else 0
        t_time = stats['time'] / stats['total'] if stats['total'] > 0 else 0
        print(f"   {type_name:<35} {stats['total']:>10} {t_acc:>9.1f}% {t_rounds:>12.2f} {t_time:>11.2f}s")
    
    return {
        'total': total,
        'correct': results['correct'],
        'accuracy': accuracy,
        'avg_rounds': avg_rounds,
        'avg_time': avg_time,
        'by_type': results['by_type'],
        'num_videos': len(results['by_video'])
    }

def main():
    base_path = os.path.dirname(os.path.abspath(__file__))
    
    # Analyze robot dataset
    robot_path = os.path.join(base_path, 'results', 'baseline', 'index_robot.jsonl')
    robot_results = analyze_jsonl(robot_path, 'Robot')
    robot_summary = print_summary(robot_results, 'Robot')
    
    # Analyze web dataset
    web_path = os.path.join(base_path, 'results', 'baseline', 'index_web.jsonl')
    web_results = analyze_jsonl(web_path, 'Web')
    web_summary = print_summary(web_results, 'Web')
    
    # Combined summary
    print(f"\n{'='*60}")
    print(f" Combined Summary - Baseline Model")
    print(f"{'='*60}")
    print(f"\n{'Dataset':<15} {'Questions':>10} {'Accuracy':>12} {'Avg Rounds':>12} {'Avg Time':>12}")
    print(f"{'-'*61}")
    if robot_summary:
        print(f"{'Robot':<15} {robot_summary['total']:>10} {robot_summary['accuracy']:>11.2f}% {robot_summary['avg_rounds']:>12.2f} {robot_summary['avg_time']:>11.2f}s")
    if web_summary:
        print(f"{'Web':<15} {web_summary['total']:>10} {web_summary['accuracy']:>11.2f}% {web_summary['avg_rounds']:>12.2f} {web_summary['avg_time']:>11.2f}s")
    
    # Total
    if robot_summary and web_summary:
        total_q = robot_summary['total'] + web_summary['total']
        total_correct = robot_summary['correct'] + web_summary['correct']
        total_acc = total_correct / total_q * 100
        total_rounds = (robot_summary['avg_rounds'] * robot_summary['total'] + 
                       web_summary['avg_rounds'] * web_summary['total']) / total_q
        total_time = (robot_summary['avg_time'] * robot_summary['total'] + 
                     web_summary['avg_time'] * web_summary['total']) / total_q
        print(f"{'-'*61}")
        print(f"{'TOTAL':<15} {total_q:>10} {total_acc:>11.2f}% {total_rounds:>12.2f} {total_time:>11.2f}s")
    
    print(f"\n✅ Analysis complete!")

if __name__ == '__main__':
    main()
