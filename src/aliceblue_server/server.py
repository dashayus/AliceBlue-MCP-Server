# src/weather_server/server.py
from mcp.server.fastmcp import Context, FastMCP
from smithery.decorators import smithery
from pydantic import BaseModel, Field

class ConfigSchema(BaseModel):
    unit: str = Field("celsius", description="Temperature unit (celsius or fahrenheit)")

@smithery.server(config_schema=ConfigSchema) 
def create_server(): 
    """Create and return a FastMCP server instance with session config."""
    
    server = FastMCP(name="Weather Server")

    @server.tool()
    def get_weather(city: str, ctx: Context) -> str: 
        """Get weather for a city."""
        # Access session-specific config through context
        session_config = ctx.session_config 
        
        # Use the configured temperature unit
        unit = session_config.unit
        formatted_temp = f"22°C" if unit == "celsius" else "72°F"

        return f"Weather in {city}: {formatted_temp}"

    return server