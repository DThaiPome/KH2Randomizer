from enum import Enum

from List.configDict import locationType
from List.inventory import magic, keyblade
from List.location.graph import RequirementEdge, chest, popup, LocationGraphBuilder, START_NODE
from Module.itemPlacementRestriction import ItemPlacementHelpers


class NodeId(str, Enum):
    PoohsHowse = "Pooh's Howse"
    PigletsHowse = "Piglet's Howse"
    RabbitsHowse = "Rabbit's Howse"
    KangasHowse = "Kanga's Howse"
    SpookyCave = "Spooky Cave"
    StarryHill = "Starry Hill"


class CheckLocation(str, Enum):
    PoohsHowseHundredAcreWoodMap = "Pooh's House 100 Acre Wood Map"
    PoohsHowseApBoost = "Pooh's House AP Boost"
    PoohsHowseMythrilStone = "Pooh's House Mythril Stone"
    PigletsHowseDefenseBoost = "Piglet's House Defense Boost"
    PigletsHowseApBoost = "Piglet's House AP Boost"
    PigletsHowseMythrilGem = "Piglet's House Mythril Gem"
    RabbitsHowseDrawRing = "Rabbit's House Draw Ring"
    RabbitsHowseMythrilCrystal = "Rabbit's House Mythril Crystal"
    RabbitsHowseApBoost = "Rabbit's House AP Boost"
    KangasHowseMagicBoost = "Kanga's House Magic Boost"
    KangasHowseApBoost = "Kanga's House AP Boost"
    KangasHowseOrichalcum = "Kanga's House Orichalcum"
    SpookyCaveMyhtrilGem = "Spooky Cave Mythril Gem"
    SpookyCaveApBoost = "Spooky Cave AP Boost"
    SpookyCaveOrichalcum = "Spooky Cave Orichalcum"
    SpookyCaveGuardRecipe = "Spooky Cave Guard Recipe"
    SpookyCaveMythrilCrystal = "Spooky Cave Mythril Crystal"
    SpookyCaveApBoost2 = "Spooky Cave AP Boost (2)"
    SweetMemories = "Sweet Memories"
    SpookyCaveMap = "Spooky Cave Map"
    StarryHillCosmicRing = "Starry Hill Cosmic Ring"
    StarryHillStyleRecipe = "Starry Hill Style Recipe"
    StarryHillCureElement = "Starry Hill Cure Element"
    StarryHillOrichalcumPlus = "Starry Hill Orichalcum+"


def make_graph(graph: LocationGraphBuilder):
    haw = locationType.HUNDREDAW

    poohs_howse = graph.add_location(NodeId.PoohsHowse, [
        chest(313, CheckLocation.PoohsHowseHundredAcreWoodMap, haw),
        chest(97, CheckLocation.PoohsHowseApBoost, haw),
        chest(98, CheckLocation.PoohsHowseMythrilStone, haw),
    ])
    piglets_howse = graph.add_location(NodeId.PigletsHowse, [
        chest(105, CheckLocation.PigletsHowseDefenseBoost, haw),
        chest(103, CheckLocation.PigletsHowseApBoost, haw),
        chest(104, CheckLocation.PigletsHowseMythrilGem, haw),
    ])
    rabbits_howse = graph.add_location(NodeId.RabbitsHowse, [
        chest(314, CheckLocation.RabbitsHowseDrawRing, haw),
        chest(100, CheckLocation.RabbitsHowseMythrilCrystal, haw),
        chest(101, CheckLocation.RabbitsHowseApBoost, haw),
    ])
    kangas_howse = graph.add_location(NodeId.KangasHowse, [
        chest(108, CheckLocation.KangasHowseMagicBoost, haw),
        chest(106, CheckLocation.KangasHowseApBoost, haw),
        chest(107, CheckLocation.KangasHowseOrichalcum, haw),
    ])
    spooky_cave = graph.add_location(NodeId.SpookyCave, [
        chest(110, CheckLocation.SpookyCaveMyhtrilGem, haw),
        chest(111, CheckLocation.SpookyCaveApBoost, haw),
        chest(112, CheckLocation.SpookyCaveOrichalcum, haw),
        chest(113, CheckLocation.SpookyCaveGuardRecipe, haw),
        chest(115, CheckLocation.SpookyCaveMythrilCrystal, haw),
        chest(116, CheckLocation.SpookyCaveApBoost2, haw),
        popup(284, CheckLocation.SweetMemories, haw, vanilla=keyblade.SweetMemories),
        popup(485, CheckLocation.SpookyCaveMap, haw),
    ])
    starry_hill = graph.add_location(NodeId.StarryHill, [
        chest(312, CheckLocation.StarryHillCosmicRing, haw),
        chest(94, CheckLocation.StarryHillStyleRecipe, haw),
        popup(285, CheckLocation.StarryHillCureElement, haw, vanilla=magic.Cure),
        popup(539, CheckLocation.StarryHillOrichalcumPlus, haw),
    ])

    if not graph.reverse_rando:
        graph.add_edge(START_NODE, poohs_howse)
        graph.add_edge(poohs_howse, piglets_howse, RequirementEdge(req=ItemPlacementHelpers.need_torn_pages(1)))
        graph.add_edge(piglets_howse, rabbits_howse, RequirementEdge(req=ItemPlacementHelpers.need_torn_pages(2)))
        graph.add_edge(rabbits_howse, kangas_howse, RequirementEdge(req=ItemPlacementHelpers.need_torn_pages(3)))
        graph.add_edge(kangas_howse, spooky_cave, RequirementEdge(req=ItemPlacementHelpers.need_torn_pages(4)))
        graph.add_edge(spooky_cave, starry_hill, RequirementEdge(req=ItemPlacementHelpers.need_torn_pages(5)))
    else:
        graph.add_edge(START_NODE, starry_hill)
        graph.add_edge(starry_hill, spooky_cave, RequirementEdge(req=ItemPlacementHelpers.need_torn_pages(1)))
        graph.add_edge(spooky_cave, kangas_howse, RequirementEdge(req=ItemPlacementHelpers.need_torn_pages(2)))
        graph.add_edge(kangas_howse, rabbits_howse, RequirementEdge(req=ItemPlacementHelpers.need_torn_pages(3)))
        graph.add_edge(rabbits_howse, piglets_howse, RequirementEdge(req=ItemPlacementHelpers.need_torn_pages(4)))
        graph.add_edge(piglets_howse, poohs_howse, RequirementEdge(req=ItemPlacementHelpers.need_torn_pages(5)))


def yeet_the_bear_location_names() -> list[str]:
    """ The names of the "yeet the bear" popup locations. """
    return [CheckLocation.StarryHillCureElement, CheckLocation.StarryHillOrichalcumPlus]