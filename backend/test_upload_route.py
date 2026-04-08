"""Test script to verify upload route is registered."""
import sys
sys.path.insert(0, '.')

try:
    from main import app
    
    # Get all routes
    routes = []
    for route in app.routes:
        if hasattr(route, 'path'):
            methods = list(route.methods) if hasattr(route, 'methods') else []
            routes.append({
                'path': route.path,
                'methods': methods
            })
    
    print(f"Total routes: {len(routes)}")
    print("\nUpload-related routes:")
    for route in routes:
        if 'upload' in route['path'].lower():
            print(f"  {route['path']} - Methods: {route['methods']}")
    
    # Check if /api/upload exists
    upload_route = [r for r in routes if r['path'] == '/api/upload']
    if upload_route:
        print(f"\n[OK] /api/upload route found: {upload_route[0]}")
    else:
        print("\n[FAIL] /api/upload route NOT found!")
        print("\nAll routes:")
        for route in routes[-10:]:
            print(f"  {route['path']} - {route['methods']}")
    
except Exception as e:
    import traceback
    print(f"Error: {e}")
    traceback.print_exc()
