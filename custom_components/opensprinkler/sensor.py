"""OpenSprinkler integration."""
import logging
from typing import Callable

from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import Entity
from homeassistant.util import slugify
from homeassistant.util.dt import utc_from_timestamp

from . import (
    OpenSprinklerControllerEntity,
    OpenSprinklerSensor,
    OpenSprinklerStationEntity,
)
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: dict,
    async_add_entities: Callable,
):
    """Set up the OpenSprinkler sensors."""
    entities = _create_entities(hass, entry)
    async_add_entities(entities)


def _create_entities(hass: HomeAssistant, entry: dict):
    entities = []

    controller = hass.data[DOMAIN][entry.entry_id]["controller"]
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    name = entry.data[CONF_NAME]
    
    # <JRJ> Test logging
    #_LOGGER.debug("Sensor::_create_entities: Debug -> Test Logging Name: %s", name)  # No output in HA log file
    #_LOGGER.info("Sensor::_create_entities:  Info  -> Test Logging Name: %s", name)  # No output in HA log file
    #_LOGGER.warning("Sensor::_create_entities: Warn -> Test Logging Name: %s", name) # Shows in HA log file
    #_LOGGER.error("Sensor::_create_entities: Error -> Test Logging Name: %s", name)  # Shows in HA log file
    #_LOGGER.critical("Sensor::_create_entities: Critical -> Test Logging Name: %s", name)  # Shows in HA log file

    entities.append(LastRunSensor(entry, name, controller, coordinator))
    #_LOGGER.warning("Sensor::_create_entities: LastRunSensor Completed")
    entities.append(RainDelayStopTimeSensor(entry, name, controller, coordinator))
    #_LOGGER.warning("Sensor::_create_entities: RainDelayStopTimeSensor Completed")
    entities.append(WaterLevelSensor(entry, name, controller, coordinator))
    #_LOGGER.warning("Sensor::_create_entities: WaterLevelSensor Completed")
    entities.append(FlowRateSensor(entry, name, controller, coordinator))
    #_LOGGER.warning("Sensor::_create_entities: FlowRateSensor Completed")
    entities.append(CurrentDrawSensor(entry, name, controller, coordinator))
    #_LOGGER.warning("Sensor::_create_entities: CurrentDrawSensor Completed")
    entities.append(ControllerCurrentTimeSensor(entry, name, controller, coordinator))
    #_LOGGER.warning("Sensor::_create_entities: ControllerCurrentTimeSensor Completed")
    entities.append(PauseEndTimeSensor(entry, name, controller, coordinator))
    #_LOGGER.warning("Sensor::_create_entities: PauseEndTimeSensor Completed")

    for _, station in controller.stations.items():
        entities.append(StationStatusSensor(entry, name, station, coordinator))
        #_LOGGER.warning("Sensor::_create_entities: StationStatusSensor Completed Station: %s", station.name)

    return entities


class WaterLevelSensor(OpenSprinklerControllerEntity, OpenSprinklerSensor, Entity):
    """Represent a sensor for water level."""

    def __init__(self, entry, name, controller, coordinator):
        """Set up a new opensprinkler water level sensor."""
        self._name = name
        self._controller = controller
        self._entity_type = "sensor"
        super().__init__(entry, name, coordinator)

    @property
    def icon(self) -> str:
        """Return icon."""
        return "mdi:water-percent"

    @property
    def name(self) -> str:
        """Return the name of this sensor including the controller name."""
        return f"{self._name} Water Level"

    @property
    def unique_id(self) -> str:
        """Return a unique, Home Assistant friendly identifier for this entity."""
        #_LOGGER.warning("Sensor::WaterLevelSensor: Slugify %s", self._entry.unique_id)
        return slugify(f"{self._entry.unique_id}_{self._entity_type}_water_level")

    @property
    def unit_of_measurement(self) -> str:
        """Return the units of measurement."""
        return "%"

    @property
    def extra_state_attributes(self):
        controller = self._controller
        attributes = {}
        for attr in [
            "last_weather_call_error",
            "last_weather_call_error_name",
        ]:
            try:
                attributes[attr] = getattr(controller, attr)
            except:  # noqa: E722
                pass

        for attr in [
            "last_weather_call",
            "last_successfull_weather_call",
        ]:
            timestamp = getattr(controller, attr)
            if not timestamp:
                attributes[attr] = None
            else:
                ##attributes[attr] = utc_from_timestamp(timestamp).isoformat()
                # OpenSprinkler on UBUNTU Server (64bit) returns a 64bit unsigned long instead of the expected 32bit unsigned int
                if (timestamp <= 0xFFFFFFFF):
                  attributes[attr] = utc_from_timestamp(timestamp).isoformat()
                else:
                  attributes[attr] = utc_from_timestamp(timestamp & 0xFFFFFFFF).isoformat()

        return attributes

    def _get_state(self) -> int:
        """Retrieve latest state."""
        return self._controller.water_level


class FlowRateSensor(OpenSprinklerControllerEntity, OpenSprinklerSensor, Entity):
    """Represent a sensor for flow rate."""

    def __init__(self, entry, name, controller, coordinator):
        """Set up a new opensprinkler flow rate sensor."""
        self._name = name
        self._controller = controller
        self._entity_type = "sensor"
        super().__init__(entry, name, coordinator)

    @property
    def icon(self) -> str:
        """Return icon."""
        return "mdi:speedometer"

    @property
    def name(self) -> str:
        """Return the name of this sensor including the controller name."""
        return f"{self._name} Flow Rate"

    @property
    def unique_id(self) -> str:
        """Return a unique, Home Assistant friendly identifier for this entity."""
        #_LOGGER.warning("Sensor::FlowRateSensor: Slugify %s", self._entry.unique_id)
        return slugify(f"{self._entry.unique_id}_{self._entity_type}_flow_rate")

    @property
    def unit_of_measurement(self):
        """Return the unit of the flow rate."""
        return "L/min"

    def _get_state(self) -> int:
        """Retrieve latest state."""
        return self._controller.flow_rate


class LastRunSensor(OpenSprinklerControllerEntity, OpenSprinklerSensor, Entity):
    """Represent a sensor that for last run time."""

    def __init__(self, entry, name, controller, coordinator):
        """Set up a new opensprinkler last run sensor."""
        # <JRJ> Code fix
        self._name = name        
        self._controller = controller
        self._entity_type = "sensor"
        super().__init__(entry, name, coordinator)

    @property
    def device_class(self):
        """Return the device class."""
        return SensorDeviceClass.TIMESTAMP

    @property
    def icon(self) -> str:
        """Return icon."""
        return "mdi:history"

    @property
    def name(self) -> str:
        """Return the name of this sensor including the controller name."""
        return f"{self._name} Last Run"

    @property
    def unique_id(self) -> str:
        """Return a unique, Home Assistant friendly identifier for this entity."""
        #_LOGGER.warning("Sensor::LastRunSensor: Slugify %s", self._entry.unique_id)        
        return slugify(f"{self._entry.unique_id}_{self._entity_type}_last_run")

    @property
    def extra_state_attributes(self):
        controller = self._controller
        attributes = {}
        for attr in [
            "last_run_station",
            "last_run_program",
            "last_run_duration",
        ]:
            try:
                attributes[attr] = getattr(controller, attr)
            except:  # noqa: E722
                pass

        return attributes

    def _get_state(self):
        """Retrieve latest state."""
        last_run = self._controller.last_run_end_time

        if last_run == 0:
            return None

        ##return utc_from_timestamp(last_run).isoformat()
        # OpenSprinkler on UBUNTU Server (64bit) returns a 64bit unsigned long instead of the expected 32bit unsigned int
        try:
          return utc_from_timestamp(last_run).isoformat()
        except:
          return utc_from_timestamp(last_run & 0xFFFFFFFF).isoformat()


class RainDelayStopTimeSensor(
    OpenSprinklerControllerEntity, OpenSprinklerSensor, Entity
):
    """Represent a sensor that for rain delay stop time."""

    def __init__(self, entry, name, controller, coordinator):
        """Set up a new opensprinkler rain delay stop time sensor."""
        self._name = name
        self._controller = controller
        self._entity_type = "sensor"
        super().__init__(entry, name, coordinator)

    @property
    def device_class(self):
        """Return the device class."""
        return SensorDeviceClass.TIMESTAMP

    @property
    def icon(self) -> str:
        """Return icon."""
        return "mdi:weather-rainy"

    @property
    def name(self) -> str:
        """Return the name of this sensor including the controller name."""
        return f"{self._name} Rain Delay Stop Time"

    @property
    def unique_id(self) -> str:
        """Return a unique, Home Assistant friendly identifier for this entity."""
        #_LOGGER.warning("Sensor::RainDelayStopTimeSensor: Slugify %s", self._entry.unique_id)          
        return slugify(f"{self._entry.unique_id}_{self._entity_type}_rdst")

    def _get_state(self):
        """Retrieve latest state."""
        rdst = self._controller.rain_delay_stop_time
        if rdst == 0:
            return None

        ##return utc_from_timestamp(rdst).isoformat()
        # OpenSprinkler on UBUNTU Server (64bit) returns a 64bit unsigned long instead of the expected 32bit unsigned int
        try:
          return utc_from_timestamp(rdst).isoformat()
        except:
          return utc_from_timestamp(rdst & 0xFFFFFFFF).isoformat()


class PauseEndTimeSensor(OpenSprinklerControllerEntity, OpenSprinklerSensor, Entity):
    """Represent a sensor for the time the pause will end."""

    def __init__(self, entry, name, controller, coordinator):
        """Set up a new opensprinkler pause time remaining sensor."""
        self._name = name
        self._entity_type = "sensor"
        self._controller = controller
        super().__init__(entry, name, coordinator)

    @property
    def device_class(self):
        return SensorDeviceClass.TIMESTAMP

    @property
    def icon(self) -> str:
        return "mdi:timeline-clock"

    @property
    def name(self) -> str:
        """Return the name of this sensor including the controller name."""
        return f"{self._name} Pause End Time"

    @property
    def unique_id(self) -> str:
        """Return a unique, Home Assistant friendly identifier for this entity."""
        #_LOGGER.warning("Sensor::PauseEndTimeSensor: Slugify %s", self._entry.unique_id)          
        return slugify(f"{self._entry.unique_id}_{self._entity_type}_pt")

    def _get_state(self):
        """Retrieve latest state."""
        pt = self._controller.pause_time_remaining
        # pt is None if the sprinkler firmware does not support pausing (<2.2.0)
        # pt is 0 if the sprinkler firmware supports pausing, but is not currently paused.
        if pt is None or pt == 0:
            return None

        # Since the controller provides the remaining time as a duration, add it to the
        # current device time to determine when the pause will end.

        ##return utc_from_timestamp(self._controller.device_time + pt).isoformat()
        # OpenSprinkler on UBUNTU Server (64bit) returns a 64bit unsigned long instead of the expected 32bit unsigned int
        if (self._controller.device_time <= 0xFFFFFFFF):
          return utc_from_timestamp(self._controller.device_time + pt).isoformat()
        else:
          return utc_from_timestamp((self._controller.device_time & 0xFFFFFFFF) + pt).isoformat()


class StationStatusSensor(OpenSprinklerStationEntity, OpenSprinklerSensor, Entity):
    """Represent a sensor for status of station."""

    def __init__(self, entry, name, station, coordinator):
        """Set up a new OpenSprinkler station sensor."""
        # <JRJ> Grab the controller ID e.g. "OpenSprinkler HA-RPI4B" or "OpenSprinkler FrontYard" to be used to generate the sensor name below
        self._name = name
        self._station = station
        self._entity_type = "sensor"
        super().__init__(entry, name, coordinator)

    # <JRJ> Original Code
    #@property
    #def name(self) -> str:
    #    """Return the name of this sensor."""
    #    return self._station.name + " Station Status"

    # <JRJ> Modified 2024-03-02: Name with controller ID e.g. FY-S00-NorthSideCedars Station Status ==> OpenSprinkler FrontYard S00 Station Status
    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        result = self._name + " S" + str(f'{self._station.index:02}') + " Station Status"
        #To enable logging:
        #   Add=> custom_components.opensprinkler: debug to configuration.yaml
        #   Add=> custom_components.pyopensprinkler: debug to configuration.yaml
        #_LOGGER.warning("Sensor: New Name: %s", result)
        return result

    @property
    def unique_id(self) -> str:
        """Return a unique, Home Assistant friendly identifier for this entity."""
        #_LOGGER.debug("Sensor: Unique Identifier: %s", slugify(f"{self._entry.unique_id}_{self._entity_type}_station_status_{self._station.index}"))
        #_LOGGER.warning("Sensor::StationStatusSensor: Slugify %s", (f"{self._entry.unique_id}_{self._entity_type}_station_status_{self._station.index}"))
        #_LOGGER.warning("Sensor::StationStatusSensor: Slugified %s", slugify(f"{self._entry.unique_id}_{self._entity_type}_station_status_{self._station.index}"))          
        return slugify(
            f"{self._entry.unique_id}_{self._entity_type}_station_status_{self._station.index}"
        )

    @property
    def icon(self) -> str:
        """Return icon."""
        if self._station.is_master:
            if self.state == "master_engaged":
                return "mdi:water-pump"
            else:
                return "mdi:water-pump-off"

        if self._station.is_running:
            return "mdi:valve-open"

        return "mdi:valve-closed"

    def _get_state(self) -> str:
        """Retrieve latest state."""
        return self._station.status


class CurrentDrawSensor(OpenSprinklerControllerEntity, OpenSprinklerSensor, Entity):
    """Represent a sensor for total current draw of all zones."""

    def __init__(self, entry, name, controller, coordinator):
        """Set up a new opensprinkler current draw sensor."""
        self._name = name
        self._controller = controller
        self._entity_type = "sensor"
        super().__init__(entry, name, coordinator)

    @property
    def icon(self) -> str:
        """Return icon."""
        return "mdi:meter-electric-outline"

    @property
    def name(self) -> str:
        """Return the name of this sensor including the controller name."""
        return f"{self._name} Current Draw"

    @property
    def unique_id(self) -> str:
        """Return a unique, Home Assistant friendly identifier for this entity."""
        #_LOGGER.warning("Sensor::CurrentDrawSensor: Slugify %s", self._entry.unique_id)           
        return slugify(f"{self._entry.unique_id}_{self._entity_type}_current_draw")

    @property
    def unit_of_measurement(self) -> str:
        """Return the units of measurement."""
        return "mA"

    def _get_state(self) -> int:
        """Retrieve latest state."""
        return self._controller.current_draw


class ControllerCurrentTimeSensor(
    OpenSprinklerControllerEntity, OpenSprinklerSensor, Entity
):
    """Represent a sensor for the controller current time."""

    def __init__(self, entry, name, controller, coordinator):
        """Set up a new opensprinkler controller current time sensor."""
        # <JRJ> Code fix
        self._name = name
        self._controller = controller
        self._entity_type = "sensor"
        super().__init__(entry, name, coordinator)

    @property
    def device_class(self):
        """Return the device class."""
        return SensorDeviceClass.TIMESTAMP

    @property
    def icon(self) -> str:
        """Return icon."""
        return "mdi:clock-check"

    @property
    def name(self) -> str:
        """Return the name of this sensor including the controller name."""
        return f"{self._name} Current Time"

    @property
    def unique_id(self) -> str:
        """Return a unique, Home Assistant friendly identifier for this entity."""
        #_LOGGER.warning("Sensor::ControllerCurrentTimeSensor: Slugify %s", self._entry.unique_id)           
        return slugify(f"{self._entry.unique_id}_{self._entity_type}_devt")

    @property
    def entity_registry_enabled_default(self) -> bool:
        """Set entity disabled by default."""
        return False

    def _get_state(self):
        """Retrieve latest state."""
        devt = self._controller.device_time
        if devt == 0:
            return None

        ##return utc_from_timestamp(devt).isoformat()
        # OpenSprinkler on UBUNTU Server (64bit) returns a 64bit unsigned long instead of the expected 32bit unsigned int
        if (self._controller.device_time <= 0xFFFFFFFF):
          return utc_from_timestamp(devt).isoformat()
        else:
          return utc_from_timestamp(devt & 0xFFFFFFFF).isoformat()
