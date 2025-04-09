import dash
import dash_bootstrap_components as dbc
import dash_leaflet as dl
from dash import html, dcc
from dash.dependencies import Input, Output, State
import time
import heapq
import osmnx as ox
import numpy as np
from functools import lru_cache
import logging
from typing import Dict, List, Tuple, Optional, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# =============================================================================
# Graph and Geometry Setup
# =============================================================================
class GraphHandler:
    def __init__(self, filename: str):
        """Initialize the graph handler with a GraphML file.
        
        Args:
            filename: Path to the GraphML file to load
        """
        self.graph = ox.load_graphml(filename)
        self.node_coords = {n: (data['y'], data['x']) for n, data in self.graph.nodes(data=True)}
        self._setup_edge_geometries()
        
    def _setup_edge_geometries(self) -> None:
        """Set up edge geometries for faster lookup during visualization."""
        self.edge_geometries_dict = {}

        for u, v, k, data in self.graph.edges(keys=True, data=True):
            try:
                if 'geometry' in data:
                    if hasattr(data['geometry'], 'coords'):
                        coords = [
                            (point[1], point[0]) if isinstance(point, tuple) else (point.y, point.x) 
                            for point in data['geometry'].coords
                        ]
                    elif isinstance(data['geometry'], list):
                        coords = [
                            (point[1], point[0]) if isinstance(point, tuple) else (point.y, point.x) 
                            for point in data['geometry']
                        ]
                    else:
                        coords = [self.node_coords[u], self.node_coords[v]]
                else:
                    coords = [self.node_coords[u], self.node_coords[v]]
                self.edge_geometries_dict[(u, v, k)] = tuple(coords)
            except (AttributeError, IndexError, TypeError) as e:
                logger.debug(f"Error processing edge geometry ({u}, {v}, {k}): {e}")
                self.edge_geometries_dict[(u, v, k)] = (self.node_coords[u], self.node_coords[v])
    
    @lru_cache(maxsize=10000)
    def get_edge_geometry(self, u: int, v: int) -> List[Tuple[float, float]]:
        """Get geometry for edge between nodes u and v.
        
        Args:
            u: Source node ID
            v: Target node ID
            
        Returns:
            List of (lat, lng) coordinates representing the edge geometry
        """
        for k in range(3):  # Most graphs won't have more than 3 parallel edges
            if (u, v, k) in self.edge_geometries_dict:
                return list(self.edge_geometries_dict[(u, v, k)])
            if (v, u, k) in self.edge_geometries_dict:
                return list(reversed(self.edge_geometries_dict[(v, u, k)]))
        if u in self.node_coords and v in self.node_coords:
            return [self.node_coords[u], self.node_coords[v]]
        return []

    def nearest_node(self, lng: float, lat: float) -> int:
        """Find the nearest node to given coordinates.
        
        Args:
            lng: Longitude
            lat: Latitude
            
        Returns:
            ID of the nearest node
        """
        return ox.distance.nearest_nodes(self.graph, X=lng, Y=lat)

# =============================================================================
# A* Search Algorithm
# =============================================================================
class AStarSearch:
    def __init__(self, graph_handler: GraphHandler, heuristic_weight: float = 1.2):
        """Initialize A* search with a graph handler.
        
        Args:
            graph_handler: GraphHandler instance
            heuristic_weight: Weight for the heuristic component of A* (default: 1.2)
        """
        self.graph_handler = graph_handler
        self.heuristic_weight = heuristic_weight
        
    def search(self, start: int, goal: int) -> Tuple[Optional[List[int]], List[Tuple[int, int]], 
                                                     List[int], List[List[Tuple[float, float]]],
                                                     Optional[List[List[Tuple[float, float]]]]]:
        """Perform A* search from start to goal.
        
        Args:
            start: Start node ID
            goal: Goal node ID
            
        Returns:
            Tuple of (path, visited_edges, visited_nodes, edge_geometries, path_geometries)
            where path is a list of node IDs or None if no path exists
        """
        graph = self.graph_handler.graph
        node_coords = self.graph_handler.node_coords
        get_edge_geometry = self.graph_handler.get_edge_geometry
        
        # Initialize data structures
        open_set = [(0, start)]
        visited = set()
        g_score = {start: 0}
        came_from = {}
        
        goal_y, goal_x = graph.nodes[goal]['y'], graph.nodes[goal]['x']
        
        visited_nodes = []
        visited_edges = []
        edge_geometries = []
        
        # Calculate heuristic for start node
        start_h = ox.distance.great_circle(
            graph.nodes[start]['y'], graph.nodes[start]['x'],
            goal_y, goal_x
        )
        f_score = {start: start_h}
        
        # Main search loop
        while open_set:
            _, current = heapq.heappop(open_set)
            if current in visited:
                continue
                
            visited.add(current)
            visited_nodes.append(current)
            
            # Goal check
            if current == goal:
                # Reconstruct path
                path = [current]
                while current in came_from:
                    current = came_from[current]
                    path.append(current)
                path.reverse()
                
                # Get path geometries
                path_geometries = []
                for i in range(len(path) - 1):
                    path_geometries.append(get_edge_geometry(path[i], path[i+1]))
                return path, visited_edges, visited_nodes, edge_geometries, path_geometries
            
            # Process neighbors
            for neighbor in graph.neighbors(current):
                if neighbor in visited:
                    continue
                    
                visited_edges.append((current, neighbor))
                edge_geometries.append(get_edge_geometry(current, neighbor))
                
                # Get edge data and calculate new score
                edge_data = graph.get_edge_data(current, neighbor)[0]
                new_g = g_score[current] + edge_data.get("length", 1)
                
                # Update if we found a better path
                if new_g < g_score.get(neighbor, float('inf')):
                    came_from[neighbor] = current
                    g_score[neighbor] = new_g
                    
                    # Calculate heuristic
                    h = self.heuristic_weight * ox.distance.great_circle(
                        graph.nodes[neighbor]['y'], graph.nodes[neighbor]['x'],
                        goal_y, goal_x
                    )
                    f_score[neighbor] = new_g + h
                    heapq.heappush(open_set, (f_score[neighbor], neighbor))
        
        # No path found
        return None, visited_edges, visited_nodes, edge_geometries, None

# =============================================================================
# GeoJSON Helper Functions
# =============================================================================
class GeoJSONGenerator:
    @staticmethod
    def create_geojson_features(geometries: List[List[Tuple[float, float]]], 
                              color: str = "red", 
                              weight: int = 2, 
                              opacity: float = 0.7) -> List[Dict[str, Any]]:
        """Create GeoJSON features from geometries.
        
        Args:
            geometries: List of geometries, each as a list of (lat, lng) coordinates
            color: Line color
            weight: Line weight
            opacity: Line opacity
            
        Returns:
            List of GeoJSON feature objects
        """
        features = []
        for geom in geometries:
            if not geom:
                continue
            coordinates = [[lng, lat] for lat, lng in geom]
            feature = {
                "type": "Feature",
                "geometry": {"type": "LineString", "coordinates": coordinates},
                "properties": {"color": color, "weight": weight, "opacity": opacity}
            }
            features.append(feature)
        return features

    @staticmethod
    def create_geojson(geometries: List[List[Tuple[float, float]]], 
                     color: str = "red", 
                     weight: int = 2, 
                     opacity: float = 0.7, 
                     chunk_size: int = 200) -> List[Dict[str, Any]]:
        """Create chunked GeoJSON objects from geometries.
        
        Args:
            geometries: List of geometries, each as a list of (lat, lng) coordinates
            color: Line color
            weight: Line weight
            opacity: Line opacity
            chunk_size: Number of features per chunk
            
        Returns:
            List of GeoJSON objects, chunked to reduce browser load
        """
        all_features = GeoJSONGenerator.create_geojson_features(geometries, color, weight, opacity)
        chunked_geojsons = []
        for i in range(0, len(all_features), chunk_size):
            chunk = all_features[i:i + chunk_size]
            chunked_geojsons.append({"type": "FeatureCollection", "features": chunk})
        return chunked_geojsons

# =============================================================================
# App State Management
# =============================================================================
class AppState:
    def __init__(self):
        """Initialize application state."""
        self.start_node = None
        self.end_node = None
        self.click_counter = 0
        self.visited_edges = []
        self.edge_geometries = []
        self.path_geometries = []
        self.chunked_geojsons = []
        self.processed_chunks = 0
        self.animation_complete = False
        
    def reset(self) -> None:
        """Reset application state."""
        self.start_node = None
        self.end_node = None
        self.click_counter = 0
        self.visited_edges = []
        self.edge_geometries = []
        self.path_geometries = []
        self.chunked_geojsons = []
        self.processed_chunks = 0
        self.animation_complete = False
        
    def get_search_data(self) -> Dict[str, Any]:
        """Get current search data for the Dash store.
        
        Returns:
            Dictionary of search data
        """
        return {
            "edges_processed": min(self.processed_chunks * len(self.chunked_geojsons), len(self.visited_edges)) 
                               if self.chunked_geojsons else 0,
            "total_edges": len(self.visited_edges),
            "path_found": bool(self.path_geometries),
            "animation_complete": self.animation_complete
        }

# =============================================================================
# Initialize App with Bootstrap
# =============================================================================
class PathfindingApp:
    def __init__(self, graph_file: str, default_center: List[float], bounds: List[List[float]]):
        """Initialize the A* pathfinding application.
        
        Args:
            graph_file: Path to the GraphML file
            default_center: Default map center [lat, lng]
            bounds: Map bounds [[min_lat, min_lng], [max_lat, max_lng]]
        """
        self.external_stylesheets = [dbc.themes.BOOTSTRAP]
        self.app = dash.Dash(__name__, 
                           suppress_callback_exceptions=True, 
                           external_stylesheets=self.external_stylesheets)
        
        # Initialize components
        self.graph_handler = GraphHandler(graph_file)
        self.astar = AStarSearch(self.graph_handler)
        self.geojson_generator = GeoJSONGenerator()
        self.state = AppState()
        
        # Map settings
        self.default_center = default_center
        self.bounds = bounds
        
        # Create the app layout
        self._create_layout()
        # Register callbacks
        self._register_callbacks()
        
    def _create_layout(self) -> None:
        """Create the app layout."""
        self.app.layout = dbc.Container([
            dbc.Row([
                dbc.Col(html.H2("A* Search Map Visualization"), width=12)
            ], className="mt-3"),
            
            dbc.Row([
                dbc.Col(
                    dl.Map([
                        dl.TileLayer(),
                        dl.LayerGroup(id="markers"),
                        dl.LayerGroup(id="visited-edges-layer"),
                        dl.LayerGroup(id="final-path-layer"),
                        dl.LayerGroup(id="points-layer")
                    ],
                    id="map",
                    center=self.default_center,
                    maxBounds=self.bounds,
                    zoom=12,
                    minZoom=12,
                    style={'width': '100%', 'height': '700px'}),
                    xs=12, lg=8
                ),
                
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Instructions"),
                        dbc.CardBody([
                            html.P("Click on the map to set the start (first click) and destination (second click) points.", 
                                 className="card-text")
                        ])
                    ], className="mb-3"),
                    
                    dbc.Card([
                        dbc.CardHeader("Actions"),
                        dbc.CardBody([
                            dbc.Button("Run Search", id="run-btn", color="primary", 
                                     className="mb-2 me-2 btn-block"),
                            dbc.Button("Clear Map", id="clear-btn", color="secondary", 
                                     className="mb-2 btn-block")
                        ])
                    ], className="mb-3"),
                    
                    dbc.Card([
                        dbc.CardHeader("Settings"),
                        dbc.CardBody([
                            html.Div([
                                dbc.Label("Animation Speed"),
                                dcc.Slider(
                                    id="speed-slider",
                                    min=500,
                                    max=950,
                                    step=50,
                                    value=800,
                                    marks={ 500: 'Slow', 750: 'Medium', 950: 'Fast (laggy)' }
                                )
                            ], className="mb-3"),
                            html.Div([
                                dbc.Label("Chunks Per Frame"),
                                dcc.Slider(
                                    id="chunks-per-frame-slider",
                                    min=1,
                                    max=5,
                                    step=1,
                                    value=1,
                                    marks={1: '1', 5: '5'}
                                )
                            ], className="mb-3"),
                            html.Div([
                                dbc.Label("Chunk Size"),
                                dcc.Slider(
                                    id="chunk-size-slider",
                                    min=1,
                                    max=300,
                                    step=50,
                                    value=100,
                                    marks={1: '1', 100: '100', 200: '200', 300: '300'}
                                )
                            ], className="mb-3"),
                            html.Div([
                                dbc.Label("Max Edges to Display"),
                                dcc.Slider(
                                    id="max-edges-slider",
                                    min=1000,
                                    max=20000,
                                    step=1000,
                                    value=5000,
                                    marks={1000: '1K', 5000: '5K', 10000: '10K (laggy)', 20000: '20K (very laggy)'}
                                )
                            ], className="mb-3")
                        ])
                    ], className="mb-3"),
                    
                    dbc.Card([
                        dbc.CardHeader("Status"),
                        dbc.CardBody([
                            html.Div(id="status", className="text-success")
                        ])
                    ])
                ], xs=12, lg=4)
            ], className="mt-3"),
            
            dcc.Interval(id="animation-interval", interval=200, n_intervals=0, disabled=True),
            dcc.Store(id="search-data", data={
                "edges_processed": 0,
                "total_edges": 0,
                "path_found": False,
                "animation_complete": False
            })
        ], fluid=True)
    
    def _register_callbacks(self) -> None:
        """Register all app callbacks."""
        # Update animation interval based on speed slider
        @self.app.callback(
            Output("animation-interval", "interval"),
            Input("speed-slider", "value")
        )
        def update_interval(value: int) -> int:
            return 1000 - value

        # Handle map clicks to set start/end points
        @self.app.callback(
            Output("markers", "children"),
            Input("map", "clickData"),
            State("markers", "children"),
            prevent_initial_call=True
        )
        def handle_map_click(click_data: Dict[str, Any], markers: List) -> List:
            if not click_data:
                return markers or []
            try:
                lat = click_data.get('latlng', {}).get('lat')
                lng = click_data.get('latlng', {}).get('lng')
                if not (lat and lng):
                    return markers or []
                    
                markers = markers or []
                markers.append(dl.Marker(position=[lat, lng]))
                self.state.click_counter += 1
                
                if self.state.click_counter == 1:
                    self.state.start_node = self.graph_handler.nearest_node(lng, lat)
                elif self.state.click_counter == 2:
                    self.state.end_node = self.graph_handler.nearest_node(lng, lat)
                elif self.state.click_counter > 2:
                    # Reset start/end and begin new selection
                    markers = [markers[-1]]
                    self.state.start_node = self.graph_handler.nearest_node(lng, lat)
                    self.state.end_node = None
                    self.state.click_counter = 1
                    
                return markers
            except Exception as e:
                logger.error(f"Error handling map click: {e}")
                return markers or []

        # Clear the map and reset state
        @self.app.callback(
            [Output("markers", "children", allow_duplicate=True),
             Output("visited-edges-layer", "children", allow_duplicate=True),
             Output("final-path-layer", "children", allow_duplicate=True),
             Output("points-layer", "children", allow_duplicate=True),
             Output("status", "children", allow_duplicate=True),
             Output("search-data", "data", allow_duplicate=True)],
            Input("clear-btn", "n_clicks"),
            prevent_initial_call=True
        )
        def clear_map(n_clicks: int) -> Tuple[List, List, List, List, str, Dict[str, Any]]:
            if n_clicks > 0:
                self.state.reset()
                search_data = {
                    "edges_processed": 0,
                    "total_edges": 0,
                    "path_found": False,
                    "animation_complete": False
                }
                return [], [], [], [], "Map cleared. Click to set new points.", search_data
            return [], [], [], [], "", {}

        # Run the A* search
        @self.app.callback(
            [Output("status", "children"),
             Output("animation-interval", "disabled"),
             Output("points-layer", "children"),
             Output("search-data", "data")],
            [Input("run-btn", "n_clicks"),
             Input("chunk-size-slider", "value"),
             Input("max-edges-slider", "value")],
            State("search-data", "data"),
            prevent_initial_call=True
        )
        def run_search(n_clicks: int, chunk_size: int, max_edges: int, search_data: Dict[str, Any]) -> Tuple[str, bool, List, Dict[str, Any]]:
            if n_clicks == 0 or not self.state.start_node or not self.state.end_node:
                return "Set start and end points and click Run Search.", True, [], search_data
                
            # Reset state for new search
            self.state.processed_chunks = 0
            self.state.animation_complete = False
            self.state.chunked_geojsons = []
            
            # Create markers for start/end nodes
            points = []
            if self.state.start_node in self.graph_handler.node_coords:
                start_lat, start_lng = self.graph_handler.node_coords[self.state.start_node]
                points.append(dl.CircleMarker(
                    center=[start_lat, start_lng], radius=5,
                    color="#007bff", fill=True, fillOpacity=1
                ))
            if self.state.end_node in self.graph_handler.node_coords:
                end_lat, end_lng = self.graph_handler.node_coords[self.state.end_node]
                points.append(dl.CircleMarker(
                    center=[end_lat, end_lng], radius=5,
                    color="green", fill=True, fillOpacity=1
                ))
                
            # Run A* search
            start_time = time.time()
            path, edges, nodes, geom, path_geom = self.astar.search(
                self.state.start_node, self.state.end_node
            )
            execution_time = time.time() - start_time

            # Store actual edge count before sampling
            actual_edge_count = len(edges) if edges else 0

            # Sample edges for visualization if needed
            if edges and actual_edge_count > max_edges:
                sample_indices = np.linspace(0, actual_edge_count - 1, max_edges, dtype=int)
                edges = [edges[i] for i in sample_indices]
                geom = [geom[i] for i in sample_indices] if geom else []
                
            if path:
                self.state.visited_edges = edges
                self.state.edge_geometries = geom if geom else []
                self.state.path_geometries = path_geom if path_geom else []
                
                # Generate GeoJSON chunks for animation
                if self.state.edge_geometries:
                    self.state.chunked_geojsons = self.geojson_generator.create_geojson(
                        self.state.edge_geometries,
                        color="red",
                        weight=2,
                        opacity=0.7,
                        chunk_size=chunk_size
                    )
                    
                updated_data = {
                    "edges_processed": 0,
                    "total_edges": actual_edge_count,
                    "path_found": True,
                    "animation_complete": False
                }
                
                status_msg = (
                    f"Path found with {len(path)} nodes, "
                    f"explored {actual_edge_count} edges (displaying {len(self.state.visited_edges)}) "
                    f"in {execution_time:.2f} seconds. Visualizing search process..."
                )
                return status_msg, False, points, updated_data
            else:
                updated_data = {
                    "edges_processed": 0,
                    "total_edges": actual_edge_count,
                    "path_found": False,
                    "animation_complete": True
                }
                return "No path found between selected points!", True, points, updated_data

        # Update the visualization during animation
        @self.app.callback(
            [Output("visited-edges-layer", "children"),
             Output("search-data", "data", allow_duplicate=True)],
            [Input("animation-interval", "n_intervals"),
             Input("chunk-size-slider", "value"),
             Input("chunks-per-frame-slider", "value")],
            State("search-data", "data"),
            prevent_initial_call=True
        )
        def update_visualization(n_intervals: int, chunk_size: int, chunks_per_frame: int, 
                                search_data: Dict[str, Any]) -> Tuple[List, Dict[str, Any]]:
            if self.state.animation_complete or not self.state.chunked_geojsons:
                return [], search_data
                
            total_edges = search_data.get("total_edges", 0)
            try:
                # Calculate how many chunks to show in this frame
                chunks_to_show = min(
                    len(self.state.chunked_geojsons),
                    self.state.processed_chunks + chunks_per_frame
                )
                self.state.processed_chunks = chunks_to_show
                
                # Calculate how many edges have been processed
                edges_processed = min(chunks_to_show * chunk_size, total_edges)
                
                # Check if animation is complete
                self.state.animation_complete = chunks_to_show >= len(self.state.chunked_geojsons)
                
                # Create GeoJSON layers for visible chunks
                geojson_layers = [
                    dl.GeoJSON(
                        data=self.state.chunked_geojsons[idx],
                        id=f"visited-edges-{idx}",
                        options={'style': {'color': '#007bff', 'weight': 2, 'opacity': 0.7}}
                    )
                    for idx in range(chunks_to_show)
                ]
                
                updated_data = {
                    "edges_processed": edges_processed,
                    "total_edges": total_edges,
                    "path_found": search_data.get("path_found", False),
                    "animation_complete": self.state.animation_complete
                }
                
                return geojson_layers, updated_data
            except Exception as e:
                logger.error(f"Error updating visualization: {e}")
                return [], search_data

        # Show the final path when animation is complete
        @self.app.callback(
            Output("final-path-layer", "children"),
            [Input("animation-interval", "n_intervals"),
             Input("search-data", "data")],
            prevent_initial_call=True
        )
        def show_final_path(n_intervals: int, search_data: Dict[str, Any]) -> List:
            animation_complete = search_data.get("animation_complete", False) or self.state.animation_complete
            path_found = search_data.get("path_found", False)
            
            if animation_complete and path_found and self.state.path_geometries:
                try:
                    path_features = self.geojson_generator.create_geojson_features(
                        self.state.path_geometries,
                        color="green",
                        weight=3,
                        opacity=1.0
                    )
                    geojson_obj = {"type": "FeatureCollection", "features": path_features}
                    return dl.GeoJSON(
                        data=geojson_obj,
                        id="final-path",
                        options={'style': {'color': 'green', 'weight': 4, 'opacity': 1.0}}
                    )
                except Exception as e:
                    logger.error(f"Error showing final path: {e}")
                    return []
            return []
    
    def run_server(self, **kwargs) -> None:
        """Run the Dash server.
        
        Args:
            **kwargs: Keyword arguments to pass to app.run_server()
        """
        self.app.run_server(**kwargs)

# =============================================================================
# Main Entry Point
# =============================================================================
# =============================================================================
# Map Data Download and Initialization
# =============================================================================
def download_map_data(place_name: str = "Algiers, Algeria", 
                     network_type: str = "drive",
                     filename: str = "algiers_graph.graphml") -> None:
    """Download and save map data from OpenStreetMap.
    
    Args:
        place_name: Name of the area to download (default: "Algiers, Algeria")
        network_type: Type of network ("drive", "walk", "bike", etc.)
        filename: Output filename for the GraphML file
    """
    try:
        logger.info(f"Downloading map data for {place_name}...")
        
        # Download the street network
        graph = ox.graph_from_place(place_name, network_type=network_type)
        
        # Simplify the graph (optional but recommended)
        graph = ox.simplify_graph(graph)
        
        # Save to GraphML file
        ox.save_graphml(graph, filename)
        logger.info(f"Map data saved to {filename}")
        
    except Exception as e:
        logger.error(f"Error downloading map data: {e}")
        raise

# =============================================================================
# Main Entry Point with Map Initialization
# =============================================================================
if __name__ == '__main__':
    # Configuration
    MAP_DATA_FILE = "algiers_graph.graphml"
    PLACE_NAME = "Algiers, Algeria"
    
    # Check if map data exists, download if not
    if not os.path.exists(MAP_DATA_FILE):
        logger.info("Map data not found. Downloading...")
        download_map_data(place_name=PLACE_NAME, filename=MAP_DATA_FILE)
    
    # Calculate map bounds from the downloaded data
    graph = ox.load_graphml(MAP_DATA_FILE)
    nodes = ox.graph_to_gdfs(graph, edges=False)
    min_lat, min_lng = nodes['y'].min(), nodes['x'].min()
    max_lat, max_lng = nodes['y'].max(), nodes['x'].max()
    bounds = [[min_lat, min_lng], [max_lat, max_lng]]
    default_center = [(min_lat + max_lat)/2, (min_lng + max_lng)/2]
    
    # Create and run the app
    app = PathfindingApp(
        graph_file=MAP_DATA_FILE,
        default_center=default_center,
        bounds=bounds
    )
    app.run_server(debug=False)