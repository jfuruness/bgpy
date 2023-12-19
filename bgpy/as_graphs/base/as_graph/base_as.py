from typing import Any, Optional, TYPE_CHECKING

from yamlable import yaml_info, YamlAble

if TYPE_CHECKING:
    from bgpy.simulation_engine import BGPSimplePolicy


@yaml_info(yaml_tag="AS")
class AS(YamlAble):
    """Autonomous System class. Contains attributes of an AS"""

    def __init__(
        self,
        asn: int,
        input_clique: bool = False,
        ixp: bool = False,
        peers: tuple["AS", ...] = tuple(),
        providers: tuple["AS", ...] = tuple(),
        customers: tuple["AS", ...] = tuple(),
        customer_cone_size: Optional[int] = None,
        propagation_rank: Optional[int] = None,
        policy: Optional["BGPSimplePolicy"] = None,
    ) -> None:
        # Make sure you're not accidentally passing in a string here
        self.asn: int = int(asn)

        self.peers: tuple["AS", ...] = peers
        self.providers: tuple["AS", ...] = providers
        self.customers: tuple["AS", ...] = customers

        # Read Caida's paper to understand these
        self.input_clique: bool = input_clique
        self.ixp: bool = ixp
        self.customer_cone_size: Optional[int] = customer_cone_size
        # Propagation rank. Rank leaves to clique
        self.propagation_rank: Optional[int] = propagation_rank

        # Hash in advance and only once since this gets called a lot
        self.hashed_asn = hash(self.asn)

        assert policy, "This should never be None"
        self.policy: BGPSimplePolicy = policy
        self.policy.as_ = self

    def __lt__(self, as_obj: Any) -> bool:
        if isinstance(as_obj, AS):
            return self.asn < as_obj.asn
        else:
            return NotImplemented

    def __eq__(self, as_obj: Any) -> bool:
        if isinstance(as_obj, AS):
            return self.asn == as_obj.asn
        else:
            return NotImplemented

    def __hash__(self) -> int:
        return self.hashed_asn

    @property
    def db_row(self) -> dict[str, str]:
        def asns(as_objs: tuple["AS", ...]) -> str:
            return "{" + ",".join(str(x.asn) for x in sorted(as_objs)) + "}"

        def _format(x: Any) -> str:
            if (isinstance(x, list) or isinstance(x, tuple)) and all(
                [isinstance(y, AS) for y in x]
            ):
                assert not isinstance(x, list), "these should all be tuples"
                return asns(x)  # type: ignore
            elif x is None:
                return ""
            elif any(isinstance(x, my_type) for my_type in (str, int, float)):
                return str(x)
            else:
                raise Exception(f"improper format type: {type(x)} {x}")

        return {attr: _format(getattr(self, attr)) for attr in self.db_row_keys}

    @property
    def db_row_keys(self) -> tuple[str, ...]:
        return (
            "asn",
            "peers",
            "customers",
            "providers",
            "input_clique",
            "ixp",
            "customer_cone_size",
            "propagation_rank",
            "rov_filtering",
            "rov_confidence",
            "rov_source",
            "hashed_asn",
            # Don't forget the properties
        ) + ("stubs", "stub", "multihomed", "transit")

    def __str__(self):
        return "\n".join(str(x) for x in self.db_row.items())

    @property
    def stub(self) -> bool:
        """Returns True if AS is a stub by RFC1772"""

        return len(self.neighbors) == 1

    @property
    def multihomed(self) -> bool:
        """Returns True if AS is multihomed by RFC1772"""

        return len(self.customers) == 0 and len(self.peers) + len(self.providers) > 1

    @property
    def transit(self) -> bool:
        """Returns True if AS is a transit AS by RFC1772"""

        return len(self.customers) > 1

    @property
    def stubs(self) -> tuple["AS", ...]:
        """Returns a list of any stubs connected to that AS"""

        return tuple([x for x in self.customers if x.stub])

    @property
    def neighbors(self) -> tuple["AS", ...]:
        """Returns customers + peers + providers"""

        return self.customers + self.peers + self.providers

    ##############
    # Yaml funcs #
    ##############

    def __to_yaml_dict__(self) -> dict[str, Any]:
        """This optional method is called when you call yaml.dump()"""

        return {
            "asn": self.asn,
            "customers": tuple([x.asn for x in self.customers]),
            "peers": tuple([x.asn for x in self.peers]),
            "providers": tuple([x.asn for x in self.providers]),
            "input_clique": self.input_clique,
            "ixp": self.ixp,
            "customer_cone_size": self.customer_cone_size,
            "propagation_rank": self.propagation_rank,
            "policy": self.policy,
        }

    @classmethod
    def __from_yaml_dict__(cls, dct: dict[Any, Any], yaml_tag: str):
        """This optional method is called when you call yaml.load()"""

        return cls(**dct)


# Needed for mypy type hinting
__all__ = ["AS"]