from holobot.sdk.network.resilience.exceptions.circuit_broken_error import CircuitBrokenError
from .. import WeatherClientInterface
from ..exceptions import InvalidLocationError, OpenWeatherError, QueryQuotaExhaustedError
from ..models import WeatherData
from discord.embeds import Embed
from discord_slash.context import SlashContext
from discord_slash.model import SlashCommandOptionType
from discord_slash.utils.manage_commands import create_option
from holobot.discord.sdk.commands import CommandBase, CommandInterface
from holobot.discord.sdk.utils import reply
from holobot.sdk.exceptions import InvalidOperationError
from holobot.sdk.ioc.decorators import injectable

@injectable(CommandInterface)
class GetBasicWeatherCommand(CommandBase):
    def __init__(self, weather_client: WeatherClientInterface) -> None:
        super().__init__("basic")
        self.__weather_client: WeatherClientInterface = weather_client
        self.group_name = "weather"
        self.description = "Displays the current temperature in a city."
        self.options = [
            create_option("city", "The name of the city", SlashCommandOptionType.STRING, True)
        ]
    
    async def execute(self, context: SlashContext, city: str) -> None:
        try:
            weather_data = await self.__weather_client.get_weather_data(city)
            if weather_data.temperature is None:
                await reply(context, "No information is available right now. Please, try again later.")
                return
            await reply(context, GetBasicWeatherCommand.__create_embed(weather_data))
        except InvalidLocationError:
            await reply(context, "The location you requested cannot be found. Did you make a typo?")
        except OpenWeatherError as error:
            await reply(context, f"An OpenWeather internal error has occurred (code: {error.error_code}). Please, try again later or contact your server administrator.")
        except InvalidOperationError:
            await reply(context, "OpenWeather isn't configured. Please, contact your server administrator.")
        except QueryQuotaExhaustedError:
            await reply(context, "The daily quota has been used up for the bot. Please, try again later or contact your server administrator.")
        except CircuitBrokenError:
            await reply(context, "I couldn't communicate with OpenWeather. Please, wait a few minutes and try again.")
    
    @staticmethod
    def __create_embed(weather_data: WeatherData) -> Embed:
        embed = Embed(
            title="Weather report", description=f"Information about the current weather in {weather_data.name}.", color=0xeb7d00
        ).add_field(
            name="Temperature", value=f"{weather_data.temperature:,.2f} °C"
        ).set_footer(text=f"Powered by OpenWeather")

        if weather_data.pressure is not None:
            embed.add_field(name="Pressure", value=f"{weather_data.pressure} hPa")
        if weather_data.humidity is not None:
            embed.add_field(name="Humidity", value=f"{weather_data.humidity}%")

        if weather_data.condition.condition_image_url is not None:
            embed.set_thumbnail(url=weather_data.condition.condition_image_url)
        return embed
