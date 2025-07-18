"""
Demonstration of the color system and image rendering engine.

This script shows how to use the color system and image renderer together
to create beautiful fractal images with different color palettes and effects.
"""

import numpy as np
import os
from fractal_editor.services.color_system import (
    ColorSystemManager, PresetPalettes, InterpolationMode
)
from fractal_editor.services.image_renderer import (
    RenderingEngine, RenderSettings
)


def create_sample_fractal_data():
    """Create sample fractal iteration data for demonstration."""
    # Create a simple pattern that resembles fractal iteration data
    width, height = 200, 200
    data = np.zeros((height, width))
    
    center_x, center_y = width // 2, height // 2
    
    for y in range(height):
        for x in range(width):
            # Distance from center
            dx = x - center_x
            dy = y - center_y
            distance = np.sqrt(dx*dx + dy*dy)
            
            # Create concentric circles with varying iteration counts
            if distance < 20:
                data[y, x] = 100  # Center (didn't escape)
            elif distance < 40:
                data[y, x] = int(80 + 20 * np.sin(distance * 0.3))
            elif distance < 60:
                data[y, x] = int(60 + 15 * np.cos(distance * 0.2))
            elif distance < 80:
                data[y, x] = int(40 + 10 * np.sin(distance * 0.1))
            else:
                data[y, x] = int(20 * (1 - distance / 100))
    
    return data.astype(int)


def demonstrate_color_palettes():
    """Demonstrate different color palettes."""
    print("🎨 Demonstrating Color System and Image Rendering")
    print("=" * 50)
    
    # Create sample fractal data
    iteration_data = create_sample_fractal_data()
    max_iterations = 100
    
    # Set up color system and rendering engine
    color_manager = ColorSystemManager()
    rendering_engine = RenderingEngine()
    
    # Create output directory
    output_dir = "demo_output"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Test each preset palette
    preset_names = color_manager.get_preset_names()
    print(f"📋 Available preset palettes: {', '.join(preset_names)}")
    print()
    
    for palette_name in preset_names:
        print(f"🎨 Rendering with {palette_name} palette...")
        
        # Set the palette
        color_manager.set_current_palette_by_name(palette_name)
        color_mapper = color_manager.get_color_mapper()
        rendering_engine.set_color_mapper(color_mapper)
        
        # Render and save the image
        filepath = os.path.join(output_dir, f"fractal_{palette_name.lower()}.png")
        rendering_engine.export_image(iteration_data, max_iterations, filepath)
        
        print(f"   ✅ Saved: {filepath}")
    
    print()


def demonstrate_render_settings():
    """Demonstrate different render settings."""
    print("⚙️  Demonstrating Render Settings")
    print("=" * 30)
    
    # Create sample fractal data
    iteration_data = create_sample_fractal_data()
    max_iterations = 100
    
    # Set up rendering with Fire palette
    color_manager = ColorSystemManager()
    color_manager.set_current_palette_by_name("Fire")
    color_mapper = color_manager.get_color_mapper()
    
    rendering_engine = RenderingEngine()
    rendering_engine.set_color_mapper(color_mapper)
    
    # Create output directory
    output_dir = "demo_output"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Test different render settings
    settings_tests = [
        ("normal", RenderSettings()),
        ("bright", RenderSettings(brightness=1.5)),
        ("high_contrast", RenderSettings(contrast=1.5)),
        ("gamma_corrected", RenderSettings(gamma=0.7)),
        ("no_antialiasing", RenderSettings(anti_aliasing=False)),
        ("combined_effects", RenderSettings(brightness=1.2, contrast=1.3, gamma=0.8))
    ]
    
    for name, settings in settings_tests:
        print(f"🔧 Rendering with {name} settings...")
        
        filepath = os.path.join(output_dir, f"fractal_fire_{name}.png")
        rendering_engine.export_image(
            iteration_data, max_iterations, filepath, settings=settings
        )
        
        print(f"   ✅ Saved: {filepath}")
    
    print()


def demonstrate_high_resolution():
    """Demonstrate high-resolution rendering."""
    print("🔍 Demonstrating High-Resolution Rendering")
    print("=" * 40)
    
    # Create sample fractal data
    iteration_data = create_sample_fractal_data()
    max_iterations = 100
    
    # Set up rendering with Ocean palette
    color_manager = ColorSystemManager()
    color_manager.set_current_palette_by_name("Ocean")
    color_mapper = color_manager.get_color_mapper()
    
    rendering_engine = RenderingEngine()
    rendering_engine.set_color_mapper(color_mapper)
    
    # Create output directory
    output_dir = "demo_output"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Render at different resolutions
    resolutions = [1, 2, 3]
    
    for scale in resolutions:
        print(f"📐 Rendering at {scale}x resolution...")
        
        filepath = os.path.join(output_dir, f"fractal_ocean_{scale}x.png")
        rendering_engine.export_image(
            iteration_data, max_iterations, filepath,
            high_resolution=True, scale_factor=scale
        )
        
        print(f"   ✅ Saved: {filepath}")
    
    print()


def demonstrate_custom_palette():
    """Demonstrate creating and using custom palettes."""
    print("🎨 Demonstrating Custom Color Palette")
    print("=" * 35)
    
    # Create sample fractal data
    iteration_data = create_sample_fractal_data()
    max_iterations = 100
    
    # Set up color system
    color_manager = ColorSystemManager()
    
    # Create a custom palette
    custom_palette = color_manager.create_custom_palette(
        "Custom Sunset",
        [
            (0.0, (25, 25, 112)),    # Midnight blue
            (0.3, (138, 43, 226)),   # Blue violet
            (0.5, (255, 20, 147)),   # Deep pink
            (0.7, (255, 69, 0)),     # Red orange
            (0.9, (255, 215, 0)),    # Gold
            (1.0, (255, 255, 224))   # Light yellow
        ],
        InterpolationMode.HSV
    )
    
    print(f"🎨 Created custom palette: {custom_palette.name}")
    print(f"   📊 Color stops: {len(custom_palette.color_stops)}")
    print(f"   🔄 Interpolation: {custom_palette.interpolation_mode.value}")
    
    # Set up rendering
    rendering_engine = RenderingEngine()
    color_mapper = color_manager.get_color_mapper()
    color_mapper.set_palette(custom_palette)
    rendering_engine.set_color_mapper(color_mapper)
    
    # Create output directory
    output_dir = "demo_output"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Render with custom palette
    filepath = os.path.join(output_dir, "fractal_custom_sunset.png")
    rendering_engine.export_image(iteration_data, max_iterations, filepath)
    
    print(f"   ✅ Saved: {filepath}")
    print()


def main():
    """Run all demonstrations."""
    print("🚀 Color System and Image Renderer Demo")
    print("=" * 60)
    print()
    
    try:
        demonstrate_color_palettes()
        demonstrate_render_settings()
        demonstrate_high_resolution()
        demonstrate_custom_palette()
        
        print("🎉 Demo completed successfully!")
        print(f"📁 Check the 'demo_output' directory for generated images.")
        
    except Exception as e:
        print(f"❌ Error during demo: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()