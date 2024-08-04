from typing import Optional, TYPE_CHECKING
from .shortest_path_hijack import ShortestPathHijack

if TYPE_CHECKING:
    from bgpy.simulation_engine import Announcement as Ann, BaseSimulationEngine


class FirstASNStrippingHijack(ShortestPathHijack):
    """An extension of the shortest path hijack that strips the first ASN"""

    RequiredASPAAttackerCls = FirstASNStrippingASPAAttacker

    def _get_announcements(
        self,
        *,
        engine: Optional["BaseSimulationEngine"] = None,
    ) -> tuple["Ann", ...]:
        """Returns the two announcements seeded for this engine input

        This engine input is for a prefix hijack,
        consisting of a valid prefix and invalid prefix with path manipulation
        """

        # First get the victims prefix
        victim_anns = super()._get_announcements(engine=engine)
        attacker_anns = self._get_first_asn_stripped_attacker_anns(engine=engine)
        return victim_anns + attacker_anns

    def _get_first_asn_stripped_attacker_anns(
        self,
        *,
        engine: Optional["BaseSimulationEngine"] = None,
    ) -> tuple["Ann", ...]:
        attacker_anns = self._get_shortest_path_attacker_anns()
        stripped_anns = list()
        for ann in attacker_anns:
            stripped_anns.append(
                ann.copy(
                    {
                        # Remove the attacker's ASN
                        "as_path": ann.as_path[1:],
                        # Attacker still wants the traffic
                        "next_hop_asn": neighbor_asn,
                        # Must add seed_asn since copying overwrites this
                        "seed_asn": ann.seed_asn,
                    }
                )
            )
        return tuple(stripped_anns)
