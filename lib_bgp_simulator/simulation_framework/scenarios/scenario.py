from abc import ABC, abstractmethod
import random
from ipaddress import ip_network

from lib_caida_collector import AS

from ...enums import Outcomes
from ...enums import Relationships
from ...simulation_engine import Announcement
from ...simulation_engine import BGPSimpleAS


class Scenario(ABC):
    """Contains information regarding an attack"""

    __slots__ = ("AnnCls",
                 "BaseASCls",
                 "AdoptASCls",
                 "num_attackers",
                 "num_victims",
                 "attacker_asns",
                 "victim_asns",
                 "non_default_as_cls_dict",
                 "ordered_prefix_subprefix_dict",
                 "announcements",
                 "non_default_as_cls_dict")

    def __init__(self,
                 # This is the base type of announcement for this class
                 # You can specify a different base ann
                 AnnCls=Announcement,
                 BaseASCls=BGPSimpleAS,
                 AdoptASCls=None,
                 num_attackers=1,
                 num_victims=1,
                 attacker_asns=None,
                 victim_asns=None):
        """inits attrs

        non_default_as_cls_dict is a dict of asn: AdoptASCls
        where you do __not__ include any of the BaseASCls,
        since that is the default
        """

        self.AnnCls = Announcement
        self.BaseASCls = BaseASCls
        self.AdoptASCls = AdoptASCls

        self.num_attackers = num_attackers
        self.num_victims = num_victims

        # If we are regenerating from yaml
        self.attacker_asns = attacker_asns
        self.victim_asns = victim_asns

    @property
    def graph_label(self):
        """Label that will be used on the graph"""

        return f"{self.BaseASCls.name} ({self.AdoptASCls.name} adopting)"

##############################################
# Set Attacker/Victim and Announcement Funcs #
##############################################

    def _set_attackers_victims_anns(self,
                                    engine,
                                    percent_adoption,
                                    prev_scenario):
        """Sets attackers, victims. announcements instance vars"""

        # Use the same attacker victim pair that was used previously
        if prev_scenario:
            self.attacker_asns = prev_scenario.attacker_asns
            self.victim_asns = prev_scenario.victim_asns
        # This is the first time, randomly select attacker/victim
        else:
            self._set_attackers_victims(engine,
                                        percent_adoption,
                                        prev_scenario)
        # Must call this here due to atk/vic pair being different
        self.announcements = self._get_announcements()
        self._get_ordered_prefix_subprefix_dict()

    def _set_attackers_victims(self, *args, **kwargs):
        """Sets attacker victim pair"""

        self.attacker_asns = self._get_attacker_asns(*args, **kwargs)
        self.victim_asns = self._get_victim_asns(*args, **kwargs)

    def _get_attacker_asns(self, *args, **kwargs):
        """Returns attacker ASN at random"""

        # Only run if we did not regenerate from YAML
        if self.attacker_asns is None:
            possible_attacker_asns = self._get_possible_attacker_asns(*args,
                                                                      **kwargs)
            return set(random.sample(possible_attacker_asns,
                                     self.num_attackers))
        else:
            return self.attacker_asns

    def _get_victim_asns(self, *args, **kwargs):
        """Returns victim ASN at random. Attacker can't be victim"""

        # Only run if we did not regenerate from YAML
        if self.victim_asns is None:
            possible_vic_asns = self._get_possible_victim_asns(*args, **kwargs)
            return set(random.sample(
                possible_vic_asns.difference(self.attacker_asns),
                self.num_victims))
        else:
            return self.victim_asns

    # For this, don't bother making a subclass with stubs_and_mh
    # Since it won't really create another class branch,
    # Since another dev would likely just subclass from the same place
    def _get_possible_attacker_asns(self,
                                    engine,
                                    percent_adoption,
                                    prev_scenario):
        """Returns possible attacker ASNs, defaulted from stubs_and_mh"""

        return engine.stub_or_mh_asns

    # For this, don't bother making a subclass with stubs_and_mh
    # Since it won't really create another class branch,
    # Since another dev would likely just subclass from the same place
    def _get_possible_victim_asns(self,
                                  engine,
                                  percent_adoption,
                                  prev_scenario):
        """Returns possible victim ASNs, defaulted from stubs_and_mh"""

        return engine.stub_or_mh_asns

    @abstractmethod
    def _get_announcements(self):
        """Returns announcements"""

        raise NotImplementedError

#######################
# Adopting ASNs funcs #
#######################

    def _get_non_default_as_cls_dict(self,
                                     engine,
                                     percent_adoption,
                                     prev_scenario):
        """Returns as class dict

        non_default_as_cls_dict is a dict of asn: AdoptASCls
        where you do __not__ include any of the BaseASCls,
        since that is the default

        By default, we use the previous engine input to maintain static
        adoption across trials
        """

        # No adopting ASes
        if not self.AdoptASCls:
            return dict()
        # By default, use the last engine input to maintain static
        # adoption across the graph
        elif prev_scenario:
            non_default_as_cls_dict = dict()
            for asn, OldASCls in prev_scenario.non_default_as_cls_dict.items():
                # If the ASN was of the adopting class of the last scenario,

                if OldASCls == prev_scenario.AdoptASCls:
                    non_default_as_cls_dict[asn] = self.AdoptASCls
                # Otherwise keep the AS class as it was
                # This is useful for things like ROV, etc...
                else:
                    non_default_as_cls_dict[asn] = OldASCls
        else:
            return self._get_adopting_asns_dict(engine, percent_adoption)

    def _get_adopting_asns_dict(self, engine, percent_adopt):
        """Get adopting ASNs

        By default, to get even adoption, adopt in each of the three
        subcategories
        """

        adopting_asns = list()
        subcategories = ("stub_or_mh_asns", "etc_asns", "input_clique_asns")
        for subcategory in subcategories:
            asns = getattr(engine, subcategory)
            # Remove ASes that are already pre-set
            # Ex: Attacker and victim
            # Ex: ROV Nodes (in certain situations)
            possible_adopters = asns.difference(self._preset_asns)
            # Get how many ASes should be adopting
            k = len(possible_adopters) * percent_adopt // 100
            # Round for the start and end of the graph
            # (if 0 ASes would be adopting, have 1 as adopt)
            # (If all ASes would be adopting, have all -1 adopt)
            # This feature was chosen by my professors
            if k == 0:
                k += 1
            elif k == len(possible_adopters):
                k -= 1

            adopting_asns.extend(random.sample(possible_adopters, k))
        adopting_asns += self._default_adopters
        assert len(adopting_asns) == len(set(adopting_asns))
        return {asn: self.AdoptASCls for asn in adopting_asns}

    @property
    def _default_adopters(self):
        """By default, victim always adopts"""

        return self.victim_asns

    @property
    def _default_non_adopters(self):
        """By default, attacker always does not adopt"""

        return self.attacker_asns

    @property
    def _preset_asns(self):
        """ASNs that have a preset adoption policy"""

        # Returns the union of default adopters and non adopters
        return self._default_adopters | self._default_non_adopters

    def determine_as_outcome(self, as_obj, ann):
        """Determines the outcome at an AS

        ann is most_specific_ann is the most specific prefix announcement
        that exists at that AS
        """

        if as_obj.asn in self.attacker_asns:
            return Outcomes.ATTACKER_SUCCESS
        elif as_obj.asn in self.victim_asns:
            return Outcomes.VICTIM_SUCCESS
        # End of traceback
        elif (ann is None
              or len(ann.as_path) == 1
              or ann.recv_relationship == Relationships.ORIGIN
              or ann.traceback_end):
            return Outcomes.DISCONNECTED
        else:
            return Outcomes.UNDETERMINED

#############################
# Engine Manipulation Funcs #
#############################

    def setup_engine(self,
                     engine,
                     percent_adoption,
                     prev_scenario=None):
        """Sets up engine input"""

        self._set_attackers_victims_anns(engine,
                                         percent_adoption,
                                         prev_scenario)
        self._set_engine_as_classes(engine, percent_adoption, prev_scenario)
        self._seed_engine_announcements(engine,
                                        percent_adoption,
                                        prev_scenario)
        engine.ready_to_run_round = 0

    def _set_engine_as_classes(self,
                               engine,
                               percent_adoption,
                               prev_scenario):
        """Resets Engine ASes and changes their AS class

        We do this here because we already seed from the scenario
        to allow for easy overriding. If scenario controls seeding,
        it doesn't make sense for engine to control resetting either
        and have each do half and half
        """

        # non_default_as_cls_dict is a dict of asn: AdoptASCls
        # where you do __not__ include any of the BaseASCls,
        # since that is the default
        # Only regenerate this if it's not already set (like with YAML)
        self.non_default_as_cls_dict = self._get_non_default_as_cls_dict(
            engine,
            percent_adoption,
            prev_scenario=prev_scenario)
        # Validate that this is only non_default ASes
        # This matters, because later this entire dict may be used for the next
        # scenario
        for asn, ASCls in self.non_default_as_cls_dict.items():
            assert ASCls != self.BaseASCls, "No defaults! See comment above"

        for as_obj in engine:
            # Set the AS class to be the proper type of AS
            as_obj.__class__ = self.non_default_as_cls_dict.get(as_obj.asn,
                                                                self.BaseASCls)
            # Clears all RIBs, etc
            # Reset base is False to avoid overrides base AS info (peers, etc)
            as_obj.__init__(reset_base=False)

    def _seed_engine_announcements(self, engine, *args):
        """Seeds announcement at the proper AS

        Since this is the simulator engine, we should
        never have to worry about overlapping announcements
        """

        for ann in self.announcements:
            # Get the AS object to seed at
            obj_to_seed = engine.as_dict[ann.seed_asn]
            # Ensure we aren't replacing anything
            err = "Seeding conflict"
            assert obj_to_seed._local_rib.get_ann(ann.prefix) is None, err
            # Seed by placing in the local rib
            obj_to_seed._local_rib.add_ann(ann)

    def post_propagation_hook(self, *args, **kwargs):
        """Useful hook for post propagation"""

        pass

################
# Helper Funcs #
################

    def _get_ordered_prefix_subprefix_dict(self):
        """Saves a dict of prefix to subprefixes"""

        prefixes = set([])
        for ann in self.announcements:
            prefixes.add(ann.prefix)
        # Do this here for speed
        prefixes = [ip_network(x) for x in prefixes]
        # Sort prefixes with most specific prefix first
        # Note that this must be sorted for the traceback to get the
        # most specific prefix first
        prefixes = list(sorted(prefixes, key=lambda x: x.num_addresses))

        prefix_subprefix_dict = {x: [] for x in prefixes}
        for outer_prefix, subprefix_list in prefix_subprefix_dict.items():
            for prefix in prefixes:
                if prefix.subnet_of(outer_prefix) and prefix != outer_prefix:
                    subprefix_list.append(str(prefix))
        # Get rid of ip_network
        self.ordered_prefix_subprefix_dict = {str(k): v for k, v
                                              in prefix_subprefix_dict.items()}

##############
# Yaml Funcs #
##############

    def __to_yaml_dict__(self):
        """This optional method is called when you call yaml.dump()"""

        return {"announcements": self.announcements,
                "attacker_asns": self.attacker_asns,
                "victim_asns": self.victim_asns,
                "num_victims": self.num_victims,
                "num_attackers": self.num_attackers,
                "non_default_as_cls_dict":
                    {asn: AS.subclass_to_name_dict[ASCls]
                     for asn, ASCls in self.non_default_as_cls_dict.items()}}

    @classmethod
    def __from_yaml_dict__(cls, dct, yaml_tag):
        """This optional method is called when you call yaml.load()"""

        as_classes = {asn: AS.name_to_subclass_dict[name]
                      for asn, name in dct["non_default_as_cls_dict"].items()}

        return cls(announcements=dct["announcements"],
                   attacker_asns=dct["attacker_asns"],
                   victim_asns=dct["victim_asns"],
                   num_victims=dct["num_victims"],
                   num_attackers=dct["num_attackers"],
                   non_default_as_cls_dict=as_classes)
