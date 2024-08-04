from typing import Optional, TYPE_CHECKING

from bgpy.scenarios.custom_scenarios.victims_prefix import VictimsPrefix
from bgpy.enums import Prefixes
from bgpy.enums import Timestamps


if TYPE_CHECKING:
    from bgpy.simulation_engine import Announcement as Ann, BaseSimulationEngine


class SubprefixHijack(VictimsPrefix):
    """Subprefix Hijack Scenario

    Subprefix hijack consists of a valid prefix by the victim with a roa
    then a subprefix from an attacker
    invalid by roa by length and origin
    """

    def _get_announcements(
        self,
        *,
        engine: Optional["BaseSimulationEngine"] = None,
    ) -> tuple["Ann", ...]:
        """Returns victim and attacker anns for subprefix hijack

        for subclasses of this EngineInput, you can set AnnCls equal to
        something other than Announcement
        """

        # First get victim's anns
        victim_anns = super()._get_announcements(engine=engine)
        attacker_anns = self._get_subprefix_attacker_anns(engine=engine)
        return victim_anns + attacker_anns

    def _get_subprefix_attacker_anns(
        self,
        *,
        engine: Optional["BaseSimulationEngine"] = None,
    ) -> tuple["Ann", ...]:
        """Returns subprefix announcements from the attacker"""

        anns = list()
        for attacker_asn in self.attacker_asns:
            anns.append(
                self.scenario_config.AnnCls(
                    prefix=Prefixes.SUBPREFIX.value,
                    as_path=(attacker_asn,),
                    timestamp=Timestamps.ATTACKER.value,
                )
            )
        return tuple(anns)
