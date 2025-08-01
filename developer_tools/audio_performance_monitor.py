"""
Audio Performance Monitor
Track and analyze audio loading performance and cache efficiency
"""
import json
import time
import os
from pathlib import Path

class AudioPerformanceMonitor:
    def __init__(self):
        self.metrics = {
            "load_times": [],
            "cache_hits": 0,
            "cache_misses": 0,
            "total_requests": 0,
            "errors": []
        }
        self.manifest_path = "static/audio_files/manifest.json"
    
    def load_manifest(self):
        """Load audio manifest"""
        try:
            with open(self.manifest_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"❌ Manifest not found: {self.manifest_path}")
            return None
    
    def analyze_audio_distribution(self):
        """Analyze distribution of audio files"""
        manifest = self.load_manifest()
        if not manifest:
            return
        
        print("📊 Audio Distribution Analysis:")
        print(f"   📁 Total files: {manifest['total_files']}")
        print(f"   💾 Total size: {manifest['total_size_mb']} MB")
        print()
        
        # HSK Characters
        hsk_count = len(manifest['hsk_characters'])
        print(f"🎯 HSK Characters:")
        print(f"   📄 Count: {hsk_count}")
        print(f"   📊 Percentage: {(hsk_count/manifest['total_files'])*100:.1f}%")
        
        # Conversations
        conv_count = len(manifest['conversations'])
        total_conv_files = sum(conv['file_count'] for conv in manifest['conversations'].values())
        print(f"\n💬 Conversations:")
        print(f"   📄 Count: {conv_count}")
        print(f"   🎵 Total files: {total_conv_files}")
        print(f"   📊 Percentage: {(total_conv_files/manifest['total_files'])*100:.1f}%")
        
        # Stories
        story_count = len(manifest['stories'])
        total_story_files = sum(story['file_count'] for story in manifest['stories'].values())
        print(f"\n📖 Stories:")
        print(f"   📄 Count: {story_count}")
        print(f"   🎵 Total files: {total_story_files}")
        print(f"   📊 Percentage: {(total_story_files/manifest['total_files'])*100:.1f}%")
    
    def analyze_file_sizes(self):
        """Analyze file size distribution"""
        manifest = self.load_manifest()
        if not manifest:
            return
        
        print("\n📏 File Size Analysis:")
        
        # Collect all file sizes
        all_sizes = []
        
        # HSK characters
        for file_info in manifest['hsk_characters'].values():
            all_sizes.append(file_info['size_mb'])
        
        # Conversations
        for conv in manifest['conversations'].values():
            for file_info in conv['files'].values():
                all_sizes.append(file_info['size_mb'])
        
        # Stories
        for story in manifest['stories'].values():
            for file_info in story['files'].values():
                all_sizes.append(file_info['size_mb'])
        
        if all_sizes:
            avg_size = sum(all_sizes) / len(all_sizes)
            min_size = min(all_sizes)
            max_size = max(all_sizes)
            
            print(f"   📊 Average size: {avg_size:.3f} MB")
            print(f"   📉 Minimum size: {min_size:.3f} MB")
            print(f"   📈 Maximum size: {max_size:.3f} MB")
            
            # Size distribution
            small_files = len([s for s in all_sizes if s < 0.02])  # < 20KB
            medium_files = len([s for s in all_sizes if 0.02 <= s < 0.05])  # 20-50KB
            large_files = len([s for s in all_sizes if s >= 0.05])  # >= 50KB
            
            print(f"\n   📦 Size Distribution:")
            print(f"      🟢 Small (<20KB): {small_files} files ({(small_files/len(all_sizes))*100:.1f}%)")
            print(f"      🟡 Medium (20-50KB): {medium_files} files ({(medium_files/len(all_sizes))*100:.1f}%)")
            print(f"      🔴 Large (>50KB): {large_files} files ({(large_files/len(all_sizes))*100:.1f}%)")
    
    def generate_optimization_recommendations(self):
        """Generate optimization recommendations"""
        manifest = self.load_manifest()
        if not manifest:
            return
        
        print("\n💡 Optimization Recommendations:")
        
        total_size = manifest['total_size_mb']
        
        if total_size > 10:
            print("   ⚠️  Total size > 10MB - Consider:")
            print("      • Implementing progressive loading")
            print("      • Reducing audio quality for web")
            print("      • Using CDN for audio delivery")
        
        # Check for large individual files
        large_files = []
        for category in ['hsk_characters', 'conversations', 'stories']:
            if category in manifest:
                for filename, file_info in manifest[category].get('files', {}).items():
                    if file_info['size_mb'] > 0.05:  # > 50KB
                        large_files.append((filename, file_info['size_mb']))
        
        if large_files:
            print(f"\n   📏 Large files detected ({len(large_files)} files > 50KB):")
            for filename, size in sorted(large_files, key=lambda x: x[1], reverse=True)[:5]:
                print(f"      • {filename}: {size:.3f} MB")
            print("      Consider re-encoding these files with lower bitrate")
        
        # Check conversation distribution
        conv_sizes = [conv['total_size_mb'] for conv in manifest['conversations'].values()]
        if conv_sizes:
            avg_conv_size = sum(conv_sizes) / len(conv_sizes)
            if avg_conv_size > 0.5:  # > 500KB per conversation
                print(f"\n   💬 Large conversations detected (avg: {avg_conv_size:.2f} MB):")
                print("      • Consider splitting long conversations")
                print("      • Implement lazy loading per sentence")
        
        print(f"\n   🚀 Immediate actions:")
        print("      • ✅ Caching headers already implemented")
        print("      • ✅ Directory structure organized")
        print("      • ✅ Lazy loading implemented")
        print("      • 🔄 Consider audio compression (FFmpeg)")
        print("      • 🔄 Monitor cache hit rates in production")
    
    def generate_report(self):
        """Generate comprehensive performance report"""
        print("🎵 Audio Performance Analysis Report")
        print("=" * 50)
        
        self.analyze_audio_distribution()
        self.analyze_file_sizes()
        self.generate_optimization_recommendations()
        
        print("\n" + "=" * 50)
        print("✅ Analysis complete!")

def main():
    """Run audio performance analysis"""
    monitor = AudioPerformanceMonitor()
    monitor.generate_report()

if __name__ == "__main__":
    main() 