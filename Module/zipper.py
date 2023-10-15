import base64
import io
import json
import zipfile
from itertools import accumulate
from typing import Optional

import random
import yaml

from Class.exceptions import BossEnemyException, GeneratorException
from Class.itemClass import ItemEncoder
from Class.modYml import modYml
from Class.newLocationClass import KH2Location
from Class.seedSettings import SeedSettings, ExtraConfigurationData, makeKHBRSettings
from List.DropRateIds import id_to_enemy_name
from List.ItemList import Items
from List.LvupStats import DreamWeaponOffsets
from List.configDict import itemType, locationCategory, locationType, BattleLevelOption
from List.ChestList import KH2Chest, getChestFileList, getChestVisualId
from Module import hashimage, commandmenu
from Module.RandomizerSettings import RandomizerSettings
from Module.battleLevels import BtlvViewer
from Module.cosmetics import CosmeticsMod
from Module.hints import Hints
from Module.multiworld import MultiWorldOutput
from Module.newRandomize import Randomizer, SynthesisRecipe
from Module.resources import resource_path
from Module.seedEvaluation import LocationInformedSeedValidator
from Module.spoilerLog import itemSpoilerDictionary, levelStatsDictionary, synth_recipe_dictionary, \
    weapon_stats_dictionary


def noop(self, *args, **kw):
    pass


def number_to_bytes(item):
    # for byte1, find the most significant bits from the item Id
    itemByte1 = item>>8
    # for byte0, isolate the least significant bits from the item Id
    itemByte0 = item & 0x00FF
    return itemByte0,itemByte1

def bytes_to_number(byte0, byte1=0):
    return int(byte0)+int(byte1<<8)

class SynthList():
    def __init__(self,offset,bytes):
        self.offset = offset
        self.id = bytes_to_number(bytes[0],bytes[1])
        self.reward = bytes_to_number(bytes[2],bytes[3])
        self.reward_type = bytes_to_number(bytes[4])
        self.material_type = bytes_to_number(bytes[5])
        self.material_rank = bytes_to_number(bytes[6])
        self.condition_type = bytes_to_number(bytes[7])
        self.count_needed = bytes_to_number(bytes[8],bytes[9])
        self.unlock_event_shop = bytes_to_number(bytes[10],bytes[11])

    def __str__(self):
        if self.reward_type == 1:
            return f"{self.offset}: ID{self.id} R{self.reward} RT{self.reward_type} MT{self.material_type} MR{self.material_rank} CT{self.condition_type} CN{self.count_needed}"
        else:
            return ""


class DropRates():
    def __init__(self,offset,bytes):
        self.offset = offset
        self.id = bytes_to_number(bytes[0],bytes[1])
        self.small_hp = bytes_to_number(bytes[2])
        self.big_hp = bytes_to_number(bytes[3])
        self.big_munny = bytes_to_number(bytes[4])
        self.medium_munny = bytes_to_number(bytes[5])
        self.small_munny = bytes_to_number(bytes[6])
        self.small_mp = bytes_to_number(bytes[7])
        self.big_mp = bytes_to_number(bytes[8])
        self.small_drive = bytes_to_number(bytes[9])
        self.big_drive = bytes_to_number(bytes[10])
        self.item1 = bytes_to_number(bytes[12],bytes[13])
        self.item1_chance = bytes_to_number(bytes[14],bytes[15])
        self.item2 = bytes_to_number(bytes[16],bytes[17])
        self.item2_chance = bytes_to_number(bytes[18],bytes[19])
        self.item3 = bytes_to_number(bytes[20],bytes[21])
        self.item3_chance = bytes_to_number(bytes[22],bytes[23])

    def to_yaml(self):
        data = {}
        data["Id"] = self.id
        data["SmallHpOrbs"] = self.small_hp
        data["BigHpOrbs"] = self.big_hp
        data["BigMoneyOrbs"] = self.big_munny
        data["MediumMoneyOrbs"] = self.medium_munny
        data["SmallMoneyOrbs"] = self.small_munny
        data["SmallMpOrbs"] = self.small_mp
        data["BigMpOrbs"] = self.big_mp
        data["SmallDriveOrbs"] = self.small_drive
        data["BigDriveOrbs"] = self.big_drive
        data["Item1"] = self.item1
        data["Item1Percentage"] = self.item1_chance
        data["Item2"] = self.item2
        data["Item2Percentage"] = self.item2_chance
        data["Item3"] = self.item3
        data["Item3Percentage"] = self.item3_chance
        return data

    def write(self,binary_data):
        id_bytes = number_to_bytes(self.id)
        binary_data[self.offset] = id_bytes[0]
        binary_data[self.offset+1] = id_bytes[1]
        binary_data[self.offset+2] = number_to_bytes(self.small_hp)[0]
        binary_data[self.offset+3] = number_to_bytes(self.big_hp)[0]
        binary_data[self.offset+4] = number_to_bytes(self.big_munny)[0]
        binary_data[self.offset+5] = number_to_bytes(self.medium_munny)[0]
        binary_data[self.offset+6] = number_to_bytes(self.small_munny)[0]
        binary_data[self.offset+7] = number_to_bytes(self.small_mp)[0]
        binary_data[self.offset+8] = number_to_bytes(self.big_mp)[0]
        binary_data[self.offset+9] = number_to_bytes(self.small_drive)[0]
        binary_data[self.offset+10] = number_to_bytes(self.big_drive)[0]
        
        item1_bytes = number_to_bytes(self.item1)
        binary_data[self.offset+12] = item1_bytes[0]
        binary_data[self.offset+13] = item1_bytes[1]
        item1_chances_bytes = number_to_bytes(self.item1_chance)
        binary_data[self.offset+14] = item1_chances_bytes[0]
        binary_data[self.offset+15] = item1_chances_bytes[1]
        
        item2_bytes = number_to_bytes(self.item2)
        binary_data[self.offset+16] = item2_bytes[0]
        binary_data[self.offset+17] = item2_bytes[1]
        item2_chances_bytes = number_to_bytes(self.item2_chance)
        binary_data[self.offset+18] = item2_chances_bytes[0]
        binary_data[self.offset+19] = item2_chances_bytes[1]
        
        item3_bytes = number_to_bytes(self.item3)
        binary_data[self.offset+20] = item3_bytes[0]
        binary_data[self.offset+21] = item3_bytes[1]
        item3_chances_bytes = number_to_bytes(self.item3_chance)
        binary_data[self.offset+22] = item3_chances_bytes[0]
        binary_data[self.offset+23] = item3_chances_bytes[1]

    def __str__(self):
        if True: #self.item1_chance and self.id not in id_to_enemy_name:
            dummy = ""
            return f"{self.id} {(id_to_enemy_name[self.id] if self.id in id_to_enemy_name else dummy)} \n HP ({self.small_hp},{self.big_hp}) \n MP ({self.small_mp},{self.big_mp}) \n Munny ({self.small_munny},{self.medium_munny},{self.big_munny}) \n Orbs ({self.small_drive},{self.big_drive}) Items: \n--- {self.item1} ({self.item1_chance/1.0}%)\n--- {self.item2} ({self.item2_chance/1.0}%)\n--- {self.item3} ({self.item3_chance/1.0}%)"
        elif self.id in id_to_enemy_name:
            return f"{self.id} {id_to_enemy_name[self.id]}"
        else:
            return ""



class SynthLocation():
    def __init__(self, loc, item, in_recipe: SynthesisRecipe):
        self.location = loc
        self.item = item
        self.requirements = [(0,0)]*6
        self.recipe = in_recipe
        self.unlock_rank = in_recipe.unlock_rank
        for i in range(len(self.recipe.requirements)):
            self.addReq(i, self.recipe.requirements[i].synth_item.Id, self.recipe.requirements[i].amount)

    def getStartingLocation(self):
        # header bytes + offset to the specific recipe + skip over the recipe bytes
        return 16+self.location*32+2

    def getBytes(self):
        bytes = []
        bytes = [self.unlock_rank,0] # unlock condition/rank
        item_byte0,item_byte1 = number_to_bytes(self.item)
        # add the item for this recipe
        bytes.append(item_byte0)
        bytes.append(item_byte1)
        # add the item as the upgraded version
        bytes.append(item_byte0)
        bytes.append(item_byte1)

        for req in self.requirements:
            item_byte0,item_byte1 = number_to_bytes(req[0])
            # add the item as an ingredient
            bytes.append(item_byte0)
            bytes.append(item_byte1)
            item_byte0,item_byte1 = number_to_bytes(req[1])
            # add the amount of that ingredient
            bytes.append(item_byte0)
            bytes.append(item_byte1)
        return bytes

    def addReq(self,req_number,req_item,req_amount):
        self.requirements[req_number] = (req_item,req_amount)


def invoke_khbr(enemy_options, mod, outZip):
    """A function that mimics the call to generateToZip in khbr. Splitting this out to allow for granular control of khbr's boss placement"""
    from khbr.randomizer import Randomizer as khbr
    from khbr.KH2.EnemyManager import EnemyManager
    from khbr.textutils import create_spoiler_text

    random.seed(str(enemy_options)) # seed boss/enemy with enemy options, which should include the seed name
    del enemy_options["seed_name"] #remove it so khbr doesn't complain

    khbr_randomizer = khbr()

    # get kh2's data
    game_data = khbr_randomizer._get_game('kh2')

    # make a new enemy manager with custom jsons
    game_data.enemy_manager = EnemyManager(resource_path("static/khbr_override/"))

    # ###  MANUAL STEP: updating records
    # import os
    # full_records = game_data.enemy_manager.create_enemy_records(ispc=False)
    # name = "full_enemy_records.json"
    # json.dump(full_records, open(os.path.join(resource_path("static/khbr_override/"), name), "w"), indent=4)

    # full_records = game_data.enemy_manager.create_enemy_records(ispc=True)
    # name = "full_enemy_records_pc.json"
    # json.dump(full_records, open(os.path.join(resource_path("static/khbr_override/"), name), "w"), indent=4)


    # ### DEBUGGING
    # valid_boss_replacements = {}
    # boss_list = game_data.enemy_manager.get_boss_list(enemy_options)
    # for _,source_boss in boss_list.items():
    #     valid_boss_replacements[source_boss["name"]] = []
    # for _,source_boss in boss_list.items():
    #     for __,dest_boss in boss_list.items():
    #         if source_boss["name"]!=dest_boss["name"]:
    #             if not EnemyManager.isReplacementBlocked(source_boss,dest_boss):
    #                 valid_boss_replacements[source_boss["name"]].append(dest_boss["name"])
    # with open("valid_boss_replacements.json","w") as f:
    #     json.dump(valid_boss_replacements, f, indent=4)

    # make sure the options are formatted properly
    khbr_randomizer._validate_options(khbr_randomizer.get_options_cli(game_data),enemy_options)

    # actually perform the randomization
    randomization = game_data.perform_randomization(enemy_options)

    # add the assets to the zip and mod yml
    assets = game_data.generate_files(randomization=randomization,outzip=outZip)
    mod["assets"] += assets

    # create the spoiler log
    return create_spoiler_text(game_data.spoilers)

    ### Backup old way
    # enemySpoilers = khbr().generateToZip("kh2", enemy_options, mod, outZip)
    # return enemySpoilers

class SeedZip:

    def __init__(self, settings: RandomizerSettings, randomizer: Randomizer, hints, extra_data: ExtraConfigurationData, unreachable_locations : list[KH2Location], multiworld : MultiWorldOutput = None):
        self.formattedTrsr = {}
        self.formattedLvup = {"Sora":{}}
        self.formattedBons = {}
        self.formattedFmlv = {}
        self.formattedItem = {"Stats":[]}
        self.formattedPlrp = []
        self.spoiler_log = None
        self.enemy_log = None

        if settings.dummy_forms:
            # convert the valor and final ids to their dummy values
            dummy_items = Items.getDummyFormItems()
            for a in randomizer.assignedItems:
                for d_item in dummy_items:
                    if a.item.Name == d_item.Name:
                        a.item = d_item

        self.assignTreasures(randomizer)
        self.assignLevels(settings,randomizer)
        self.assignSoraBonuses(randomizer)
        self.assignDonaldBonuses(randomizer)
        self.assignGoofyBonuses(randomizer)
        self.assignFormLevels(randomizer)
        self.assignWeaponStats(randomizer)
        self.assignStartingItems(settings, randomizer)
        for i in range(5):
            if self.createZip(settings, randomizer, hints, extra_data, unreachable_locations, multiworld):
                return
        raise BossEnemyException(f"Boss/enemy module had an unexpected error. Try different a different seed or different settings.")

    def createZip(self, settings: RandomizerSettings, randomizer: Randomizer, hints, extra_data: ExtraConfigurationData, unreachable_locations, multiworld):
        mod = modYml.getDefaultMod()
        sys = modYml.getSysYAML(settings.seedHashIcons,settings.crit_mode)

        data = io.BytesIO()
        with zipfile.ZipFile(data, "w", zipfile.ZIP_DEFLATED) as outZip:
            yaml.emitter.Emitter.process_tag = noop

            platform = extra_data.platform
            tourney_gen = extra_data.tourney
            
            pc_seed_toggle = (platform=="PC")


            def _shouldRunKHBR():
                if not settings.enemy_options.get("boss", False) in [False, "Disabled"]:
                    return True
                if not settings.enemy_options.get("enemy", False) in [False, "Disabled"]:
                    return True
                if settings.enemy_options.get("remove_damage_cap", False):
                    return True
                if settings.enemy_options.get("cups_give_xp", False):
                    return True
                if settings.enemy_options.get("retry_data_final_xemnas", False):
                    return True
                if settings.enemy_options.get("retry_dark_thorn", False):
                    return True
                if settings.enemy_options.get("costume_rando", False):
                    return True
                if settings.enemy_options.get("party_rando", False):
                    return True
                if not settings.enemy_options.get("remove_cutscenes", False) in [False, "Disabled"]:
                    return True
                if not settings.enemy_options.get("revenge_limit_rando", False) in [False, "Vanilla"]:
                    return True
                
                return False

            enemySpoilers = None
            enemySpoilersJSON = {}
            if _shouldRunKHBR():
                enemySpoilers = None
                enemySpoilersJSON = {}
            
                if platform == "PC":
                    settings.enemy_options["memory_expansion"] = True
                else:
                    settings.enemy_options["memory_expansion"] = False
                
                enemySpoilers = invoke_khbr(settings.enemy_options, mod, outZip)

                lines = enemySpoilers.split("\n")

                current_key = ""
                for line in lines:
                    if '\t' in line:
                        modded_line = line.replace('\t','')
                        enemies = modded_line.split(" became ")
                        # this is adding to the current list
                        new_entry = {}
                        new_entry["original"] = enemies[0]
                        new_entry["new"] = enemies[1]
                        enemySpoilersJSON[current_key].append(new_entry)
                    elif line!="":
                        current_key = line
                        enemySpoilersJSON[current_key] = []
                if enemySpoilersJSON:
                    outZip.writestr("enemies.rando", base64.b64encode(json.dumps(enemySpoilersJSON).encode('utf-8')).decode('utf-8'))
                    # for boss_replacement in enemySpoilersJSON["BOSSES"]:
                    #     print(f"{boss_replacement['original']} {boss_replacement['new']}")

            print("Passed boss/enemy")

            if multiworld:
                outZip.writestr("multiworld.multi", json.dumps(multiworld()))

            self.generate_seed_hash_image(settings, outZip)
            self.createPuzzleAssets(settings, randomizer, mod, outZip, pc_seed_toggle)
            self.createSynthAssets(settings, randomizer, mod, outZip, pc_seed_toggle)
            self.createASDataAssets(settings, mod, outZip)
            self.createSkipCarpetAssets(settings, mod, outZip)
            self.createMapSkipAssets(settings, mod, outZip)
            self.createBlockingSkipAssets(settings, mod, outZip)
            self.createAtlanticaSkipAssets(settings, mod, outZip)
            self.createWardrobeSkipAssets(settings, mod, outZip)
            self.createDropRateAssets(settings, randomizer, mod, outZip)
            self.createShopRandoAssets(settings, randomizer, mod, outZip, sys)
            self.createChestVisualAssets(settings, randomizer, mod, outZip)
            battle_level_spoiler = self.createBtlvRandoAssets(settings, mod, outZip)

            outZip.writestr("TrsrList.yml", yaml.dump(self.formattedTrsr, line_break="\r\n"))
            outZip.writestr("BonsList.yml", yaml.dump(self.formattedBons, line_break="\r\n"))
            outZip.writestr("LvupList.yml", yaml.dump(self.formattedLvup, line_break="\r\n"))
            outZip.writestr("FmlvList.yml", yaml.dump(self.formattedFmlv, line_break="\r\n"))
            outZip.writestr("ItemList.yml", yaml.dump(self.formattedItem, line_break="\r\n"))
            outZip.writestr("PlrpList.yml", yaml.dump(self.formattedPlrp, line_break="\r\n"))
            outZip.writestr("sys.yml", yaml.dump(sys, line_break="\r\n"))

            if hints is not None:
                Hints.writeHints(hints, "HintFile", outZip)

            self.createBetterSTTAssets(settings, mod, outZip)
            self.addCmdListModifications(settings, mod, outZip)
            
            if settings.spoiler_log or tourney_gen:
                if not tourney_gen:
                    mod["title"] += " w/ Spoiler"
                with open(resource_path("static/spoilerlog.html")) as spoiler_site:
                    settings_spoiler_json = settings.ui_settings.settings_spoiler_json()
                    synthesis_recipe_spoiler = synth_recipe_dictionary(randomizer.assignedItems, randomizer.synthesis_recipes)
                    weapon_stats_spoiler = weapon_stats_dictionary(
                        sora_assignments=randomizer.assignedItems,
                        donald_assignments=randomizer.assignedDonaldItems,
                        goofy_assignments=randomizer.assignedGoofyItems,
                        weapons=randomizer.weaponStats
                    )
                    html_template = spoiler_site.read().replace("SEED_NAME_STRING",settings.random_seed) \
                                                       .replace("{SEED_STRING}", settings.seed_string) \
                                                       .replace("LEVEL_STATS_JSON",json.dumps(levelStatsDictionary(randomizer.levelStats))) \
                                                       .replace("FORM_EXP_JSON",json.dumps({"Summon": {"multiplier": settings.summon_exp_multiplier, "values": list(accumulate(settings.summon_exp))},
                                                                                            "Valor": {"multiplier": settings.valor_exp_multiplier, "values": list(accumulate(settings.valor_exp))},
                                                                                            "Wisdom": {"multiplier": settings.wisdom_exp_multiplier, "values": list(accumulate(settings.wisdom_exp))},
                                                                                            "Limit": {"multiplier": settings.limit_exp_multiplier, "values": list(accumulate(settings.limit_exp))},
                                                                                            "Master": {"multiplier": settings.master_exp_multiplier, "values": list(accumulate(settings.master_exp))},
                                                                                            "Final": {"multiplier": settings.final_exp_multiplier, "values": list(accumulate(settings.final_exp))},})) \
                                                       .replace("DEPTH_VALUES_JSON",json.dumps(randomizer.location_weights.weights)) \
                                                       .replace("SORA_ITEM_JSON",json.dumps(itemSpoilerDictionary(randomizer.assignedItems, randomizer.shop_items, randomizer.location_weights,unreachable_locations), indent=4, cls=ItemEncoder)) \
                                                       .replace("DONALD_ITEM_JSON",json.dumps(itemSpoilerDictionary(randomizer.assignedDonaldItems), indent=4, cls=ItemEncoder))\
                                                       .replace("GOOFY_ITEM_JSON",json.dumps(itemSpoilerDictionary(randomizer.assignedGoofyItems), indent=4, cls=ItemEncoder))\
                                                       .replace("BOSS_ENEMY_JSON",json.dumps(enemySpoilersJSON)) \
                                                       .replace("BATTLE_LEVEL_JSON",json.dumps(battle_level_spoiler)) \
                                                       .replace("{SYNTHESIS_RECIPE_JSON}", json.dumps(synthesis_recipe_spoiler)) \
                                                       .replace("{WEAPON_STATS_JSON}", json.dumps(weapon_stats_spoiler)) \
                                                       .replace("{SETTINGS_JSON}", json.dumps(settings_spoiler_json))
                    html_template = html_template.replace("PromiseCharm","Promise Charm")
                    if not tourney_gen:
                        outZip.writestr("spoilerlog.html",html_template)
                    self.spoiler_log = html_template
                    self.enemy_log = enemySpoilers
                    outZip.write(resource_path("static/KHMenu.otf"), "KHMenu.otf")
                if enemySpoilers and not tourney_gen:
                    outZip.writestr("enemyspoilers.txt", enemySpoilers)

            mod["assets"] += commandmenu.randomize_command_menus(extra_data.command_menu_choice)

            music_assets, music_replacements = CosmeticsMod.randomize_music(settings.ui_settings)
            mod["assets"] += music_assets
            self.write_music_replacements(music_replacements, outZip)

            outZip.write(resource_path("Module/icon.png"), "icon.png")

            # closing the zip here, validating and adding mod.yml later
            outZip.close()
        data.seek(0)
        new_data = self.validate_mod_yml(mod,settings,data)
        self.outputZip = new_data
        return True

    def validate_mod_yml(self,mod,settings,in_data):
        print("Starting mod yml validation")
        # merge cmd mods if there are two
        #  first, find all the list patches we are assigning
        listpatch_files = []
        listpatch_contents = []
        for a in mod["assets"]:
            if a["name"]=="03system.bin":
                for index, b in enumerate(a["source"]):
                    if b["name"]=="cmd":
                        listpatch_files.append(b["source"][0]["name"].replace('\\',"/"))
        
        # if there are multiple cmd listpatches, we have to read all the contents to create new file
        if len(listpatch_files) > 1:
            with zipfile.ZipFile(in_data, "r") as current_zip:
                # for name in current_zip.namelist():
                #     print(name)
                # print("----")
                for l_file in listpatch_files:
                    # print(l_file)
                    path = zipfile.Path(current_zip, at=l_file)
                    with path.open(encoding='UTF-8') as f:
                        listpatch_contents+=yaml.safe_load(f)
                        # print(listpatch_contents)

            # remove all instances of 03_system cmd listpatches (we'll add another afterward)
            num_03system_entries = 0
            delete_system_indices = []
            for outer_index, a in enumerate(mod["assets"]):
                delete_asset_indices = []
                if a["name"]=="03system.bin":
                    num_03system_entries+=1
                    for index, b in enumerate(a["source"]):
                        if b["name"]=="cmd":
                            delete_asset_indices.append(index)
                    a["source"] = [i for j, i in enumerate(a["source"]) if j not in delete_asset_indices]
                    if len(a["source"])==0:
                        delete_system_indices.append(outer_index)
            # assumes that empty 03system lists are only happening from 
            # listpatches of cmd, and we don't want to remove the only 
            # instance of this in the yaml, so only remove empty entries 
            # if they are duplicates
            if num_03system_entries>1:
                mod["assets"] = [i for j, i in enumerate(mod["assets"]) if j not in delete_system_indices]
            
            for a in mod["assets"]:
                if a["name"]=="03system.bin":
                    a["source"].append({"method":"listpatch","name":"cmd","source":[{"name":"merged_cmd_list.yml","type":"cmd"}],"type":"list"})


        for modded_file in ["00battle.bin"]:
            first_asset_index = None
            delete_asset_indices = []
            for index,a in enumerate(mod["assets"]):
                if a["name"]==modded_file:
                    if first_asset_index:
                        delete_asset_indices.append(index)
                        # add these sources into this group
                        mod["assets"][first_asset_index]["source"]+=a["source"]
                    else:
                        first_asset_index = index
            # delete all duplicates
            mod["assets"] = [i for j, i in enumerate(mod["assets"]) if j not in delete_asset_indices]

        # # if we aren't removing damage cap, don't include khbr's enmp mod file (TODO: remove this when khbr listpatches enmp)
        # if not settings.enemy_options.get("remove_damage_cap", False):
        #     print("Removing khbr enmp file...")
        #     delete_asset_indices = []
        #     battle_index = None
        #     for index,a in enumerate(mod["assets"]):
        #         if a["name"]=="00battle.bin":
        #             battle_index = index
        #             for second_index,b in enumerate(a["source"]):
        #                 if b["name"]=="enmp":
        #                     delete_asset_indices.append(second_index)

        #     # delete enmp mod
        #     mod["assets"][battle_index]["source"] = [i for j, i in enumerate(mod["assets"][battle_index]["source"]) if j not in delete_asset_indices]
            
        # # if we aren't doing boss or enemy rando, don't include khbr's modded form msets (TODO: remove this when khbr doesn't just add these all the time)
        # if settings.enemy_options.get("boss", False) in [False, "Disabled"] and \
        #     settings.enemy_options.get("enemy", False) in [False, "Disabled"]:
        #     print("Removing khbr form msets...")
        #     offending_msets = ["obj/P_EX100_BTLF.mset",
        #                         "obj/P_EX100_HTLF.mset",
        #                         "obj/P_EX100_KH1F.mset",
        #                         "obj/P_EX100_MAGF.mset",
        #                         "obj/P_EX100_TRIF.mset",
        #                         "obj/P_EX100_ULTF.mset"]
        #     delete_asset_indices = []
        #     for index,a in enumerate(mod["assets"]):
        #         if a["name"] in offending_msets:
        #             delete_asset_indices.append(index)

        #     # delete form msets mod
        #     mod["assets"] = [i for j, i in enumerate(mod["assets"]) if j not in delete_asset_indices]
        # else:
        # add multi support for TWTNW NPCs, msg/jp/eh.bar (TODO: remove this when khbr does it on its own)
        for index,a in enumerate(mod["assets"]):
            if a["name"] == "msg/jp/eh.bar":
                a["multi"].append({"name":"msg/fr/eh.bar"})
                a["multi"].append({"name":"msg/gr/eh.bar"})
                a["multi"].append({"name":"msg/it/eh.bar"})
                a["multi"].append({"name":"msg/sp/eh.bar"})

        # now that the mod yml is proper, we want to add any merged files into the zip, along with the mod.yml
        with zipfile.ZipFile(in_data, "a", zipfile.ZIP_DEFLATED) as current_zip:
            current_zip.writestr("mod.yml", yaml.dump(mod, line_break="\r\n"))
            if len(listpatch_contents) > 0:
                current_zip.writestr("merged_cmd_list.yml", yaml.dump(listpatch_contents, line_break="\r\n"))
        in_data.seek(0)
        return in_data

    def generate_seed_hash_image(self, settings: RandomizerSettings, out_zip: zipfile.ZipFile):
        hash_icons = settings.seedHashIcons
        image_data = hashimage.generate_seed_hash_image(hash_icons, use_bitmap=False)
        out_zip.writestr('preview.png', image_data)
        out_zip.writestr('misc/randoseed-hash-icons.csv', ','.join(hash_icons))

    def createBtlvRandoAssets(self, settings, mod, outZip):
        btlv_option_name = settings.battle_level_rando

        btlv = BtlvViewer()
        btlv.use_setting(
            btlv_option_name,
            battle_level_offset=settings.battle_level_offset,
            battle_level_range=settings.battle_level_range
        )
        if (btlv_option_name == BattleLevelOption.NORMAL.name) or \
                (btlv_option_name == BattleLevelOption.OFFSET.name and settings.battle_level_offset == 0) or \
                (btlv_option_name == BattleLevelOption.RANDOM_WITHIN_RANGE.name and settings.battle_level_range == 0):
            return btlv.get_spoiler()
        for x in mod["assets"]:
            if x["name"]=="00battle.bin":
                x["source"]+=modYml.getBtlvMod()
                break
        btlv.write_modifications(outZip)
        return btlv.get_spoiler()

    def addCmdListModifications(self,settings,mod,outZip):
        if not settings.roxas_abilities_enabled and not settings.disable_final_form:
            return
        
        if settings.roxas_abilities_enabled and not settings.disable_final_form:
            cmd_yml = "better_stt/CmdList.yml"
        elif settings.roxas_abilities_enabled and settings.disable_final_form: 
            cmd_yml = "better_stt/CmdListWDisableFinal.yml"
        elif not settings.roxas_abilities_enabled and settings.disable_final_form: 
            cmd_yml = "disable_final_form.yml"
        else:
            raise Exception("Trying to get cmd list mod without disabling final or better stt")
        
        outZip.write(resource_path("static/"+cmd_yml),cmd_yml)

        for x in mod["assets"]:
            if x["name"]=="03system.bin":
                x["source"]+=modYml.getCmdListMod(cmd_yml)
                break


    def createASDataAssets(self,settings,mod,outZip):
        if settings.as_data_split:
            mod["assets"] += modYml.getASDataMod()
            outZip.write(resource_path("static/as_data_split/hb32evt.script"), "asdata/hb32evt.script")
            outZip.write(resource_path("static/as_data_split/hb33evt.script"), "asdata/hb33evt.script")
            outZip.write(resource_path("static/as_data_split/hb34evt.script"), "asdata/hb34evt.script")
            outZip.write(resource_path("static/as_data_split/hb38evt.script"), "asdata/hb38evt.script")

    def createBetterSTTAssets(self,settings,mod,outZip):
        boss_enabled = not settings.enemy_options.get("boss", False) in [False, "Disabled"]
        if settings.roxas_abilities_enabled:
            mod["assets"] += modYml.getBetterSTTMod(boss_enabled)
            outZip.write(resource_path("static/better_stt/trinity_zz.bar"), "better_stt/trinity_zz.bar")
            outZip.write(resource_path("static/better_stt/B_EX100.mset"), "better_stt/B_EX100.mset")
            outZip.write(resource_path("static/better_stt/F_TT010.mset"), "better_stt/F_TT010.mset")
            outZip.write(resource_path("static/better_stt/P_EX110.mset"), "better_stt/P_EX110.mset")
            outZip.write(resource_path("static/better_stt/W_EX010_RX.mset"), "better_stt/W_EX010_RX.mset")
            # outZip.write(resource_path("static/better_stt/ObjList_Better_STT.yml"), "better_stt/ObjList_Better_STT.yml")
            if boss_enabled:
                outZip.write(resource_path("static/better_stt/B_EX100_SR.mset"), "better_stt/B_EX100_SR.mset")
    
    def createSkipCarpetAssets(self,settings,mod,outZip):
        if settings.skip_carpet_escape:
            mod["assets"] += [modYml.getSkipCarpetEscapeMod()]
            outZip.write(resource_path("static/skip_carpet_escape.script"), "skip_carpet_escape.script")

    def createAtlanticaSkipAssets(self,settings,mod,outZip):
        if settings.atlantica_skip:
            mod["assets"] += [modYml.getAtlanticaTutorialSkipMod()]
            outZip.write(resource_path("static/atlantica_skip.script"), "atlantica_skip.script")

    def createWardrobeSkipAssets(self,settings,mod,outZip):
        if settings.wardrobe_skip:
            mod["assets"] += [modYml.getWardrobeSkipMod()]
            outZip.write(resource_path("static/wardrobe/N_BB080_BTL.mset"), "wardrobe_skip.mset")

    def createBlockingSkipAssets(self,settings,mod,outZip):
        if settings.block_cor_skip:
            mod["assets"] += [modYml.getBlockCorSkipMod()]
            outZip.write(resource_path("static/disable_cor_skip.script"), "disable_cor_skip.script")
        if settings.block_shan_yu_skip:
            mod["assets"] += [modYml.getBlockShanYuSkipMod()]
            outZip.write(resource_path("static/disable_shan_yu_skip.script"), "disable_shan_yu_skip.script")

    def createMapSkipAssets(self,settings,mod,outZip):
        if settings.pr_map_skip:
            mod["assets"] += modYml.getMapSkipMod()
            outZip.write(resource_path("static/map_skip/ca.yml"), "map_skip/ca.yml")
            outZip.write(resource_path("static/map_skip/libretto-ca.bar"), "map_skip/libretto-ca.bar")


    def createPuzzleAssets(self, settings, randomizer, mod, outZip, pc_toggle):
        if locationType.Puzzle not in settings.disabledLocations:
            mod["assets"] += [modYml.getPuzzleMod(pc_toggle)]
            assignedPuzzles = self.getAssignmentSubsetFromType(randomizer.assignedItems,[locationType.Puzzle])
            with open(resource_path("static/puzzle.bin"), "rb") as puzzleBar:
                binaryContent = bytearray(puzzleBar.read())
                for puzz in assignedPuzzles:
                    byte0 = 20+puzz.location.LocationId*16
                    byte1 = 20+puzz.location.LocationId*16+1
                    item = puzz.item.Id
                        
                    itemByte0, itemByte1 = number_to_bytes(item)
                    binaryContent[byte0] = itemByte0
                    binaryContent[byte1] = itemByte1
                outZip.writestr("modified_puzzle.bin",binaryContent)

                
    def createDropRateAssets(self, settings, randomizer, mod, outZip):
        global_jackpot = settings.global_jackpot
        global_lucky_lucky = settings.global_lucky
        fast_urns = settings.fast_urns
        rich_enemies = settings.rich_enemies
        near_unlimited_mp = settings.unlimited_mp

        if global_jackpot>0 or global_lucky_lucky>0 or fast_urns or rich_enemies or near_unlimited_mp:
            for x in mod["assets"]:
                if x["name"]=="00battle.bin":
                    x["source"].append(modYml.getDropModList())
                    break
            all_drops = {}
            testing = []
            with open(resource_path("static/drops.bin"), "rb") as dropsbar:
                binaryContent = bytearray(dropsbar.read())
                for i in range(0,184):
                    start_index = 8+24*i
                    rate = DropRates(start_index,binaryContent[start_index:start_index+24])
                    all_drops[rate.id] = rate

                    if rate.id not in id_to_enemy_name:
                        testing.append(rate.id)


            spawnable_enemy_ids = [1,2,3,4,5,6,7,8,9,10,11,12,13,15,17,18,22,23,24,25,26,27,28,29,30,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,63,64,65,66,69,73,87,88,89,96,112,171,172,173,174,175,176,177,178,179,180,181,182]
            urn_ids = [70,71]
            stt_enemies = [119,120,121,130,145]
            struggles = [122,131,132]

            modded_ids = []

            if rich_enemies: 
                for drop in all_drops.values():
                    if drop.id in spawnable_enemy_ids:
                        modded_ids.append(drop.id)
                        drop.medium_munny = max(drop.medium_munny,2)
                        drop.small_munny = max(drop.small_munny,2)
            if near_unlimited_mp: 
                for drop in all_drops.values():
                    if drop.id in spawnable_enemy_ids:
                        modded_ids.append(drop.id)
                        drop.big_mp = max(drop.big_mp,5)
                        drop.small_mp = max(drop.small_mp,5)

            if global_lucky_lucky > 0: 
                for drop in all_drops.values():
                    if drop.item1 != 0:
                        modded_ids.append(drop.id)
                        drop.item1_chance = min(drop.item1_chance + (drop.item1_chance//2)*global_lucky_lucky,100)
                    if drop.item2 != 0:
                        modded_ids.append(drop.id)
                        drop.item2_chance = min(drop.item2_chance + (drop.item2_chance//2)*global_lucky_lucky,100)
                    if drop.item3 != 0:
                        modded_ids.append(drop.id)
                        drop.item3_chance = min(drop.item3_chance + (drop.item3_chance//2)*global_lucky_lucky,100)
            if global_jackpot > 0: 
                for drop in all_drops.values():
                    modded_ids.append(drop.id)
                    drop.small_hp = min(drop.small_hp + (drop.small_hp//2)*global_jackpot,64)
                    drop.big_hp = min(drop.big_hp + (drop.big_hp//2)*global_jackpot,64)
                    drop.big_munny = min(drop.big_munny + (drop.big_munny//2)*global_jackpot,64)
                    drop.medium_munny = min(drop.medium_munny + (drop.medium_munny//2)*global_jackpot,64)
                    drop.small_munny = min(drop.small_munny + (drop.small_munny//2)*global_jackpot,64)
                    drop.small_mp = min(drop.small_mp + (drop.small_mp//2)*global_jackpot,64)
                    drop.big_mp = min(drop.big_mp + (drop.big_mp//2)*global_jackpot,64)
                    drop.small_drive = min(drop.small_drive + (drop.small_drive//2)*global_jackpot,64)
                    drop.big_drive = min(drop.big_drive + (drop.big_drive//2)*global_jackpot,64)

            if fast_urns:
                for u in urn_ids:
                    modded_ids.append(u)
                    all_drops[u].big_hp = 64

            modded_drops_data = []
            for drop in all_drops.values():
                if drop.id in modded_ids:
                    modded_drops_data.append(drop.to_yaml())

            # write changes
            outZip.writestr("przt.yml", yaml.dump(modded_drops_data, line_break="\r\n"))
            # with open(resource_path("static/drops.bin"), "rb") as dropsbar:
            #     binaryContent = bytearray(dropsbar.read())
            #     for drop in all_drops:
            #         all_drops[drop].write(binaryContent)
            #     outZip.writestr("modified_drops.bin",binaryContent)

    def createShopRandoAssets(self, settings, randomizer, mod, outZip, sys):
        if len(randomizer.shop_items)>0:
            for x in mod["assets"]:
                if x["name"]=="03system.bin":
                    x["source"].append(modYml.getShopMod())
                    break

            items_for_shop = []
            keyblade_item_ids = [i.Id for i in randomizer.shop_items if i.ItemType==itemType.KEYBLADE]
            report_item_ids = [i.Id for i in randomizer.shop_items if i.ItemType==itemType.REPORT]
            story_unlock_ids = [i.Id for i in randomizer.shop_items if i.ItemType==itemType.STORYUNLOCK]
            consumables = [i.Id for i in randomizer.shop_items if i.ItemType==itemType.ITEM]
            
            remaining_items = [i.Id for i in randomizer.shop_items if i.Id not in keyblade_item_ids+report_item_ids+story_unlock_ids+consumables]

            if len(keyblade_item_ids)>0: 
                for i in keyblade_item_ids:
                    items_for_shop.append((i,400))

            if len(report_item_ids)>0:
                for i in report_item_ids:
                    items_for_shop.append((i,75*(i-225)))
                for i in range(13):
                    sys.append({"id":46778-32768+i*2,"en":f"Ansem Report {i+1}"})

            if len(story_unlock_ids)>0:
                for i in story_unlock_ids:
                    items_for_shop.append((i,500))
            
            if len(consumables)>0:
                consumable_price_map = {4:400,7:600,274:400,275:600,276:250,277:250,278:250,279:250}
                for i in consumables:
                    if i in consumable_price_map:
                        items_for_shop.append((i,consumable_price_map[i]))
                    else:
                        items_for_shop.append((i,700))

            if len(remaining_items)>0:
                raise GeneratorException(f"Trying to put items in the shop that weren't expected: {len(remaining_items)}")
                # price_map = {itemRarity.COMMON:100,itemRarity.UNCOMMON:300, itemRarity.RARE:500, itemRarity.MYTHIC:1000}
                # for i in remaining_items:
                #     items_for_shop.append((i.Id,price_map[i.Rarity]))
        

            with open(resource_path("static/full_items.json"), "r") as itemjson:
                all_item_jsons = json.loads(itemjson.read())
                self.formattedItem["Items"] = []
                for x,price in items_for_shop:
                    item_json = None
                    for y in all_item_jsons["Items"]:
                        if y["Id"]==x:
                            item_json = y
                            break
                    item_json["ShopBuy"]=price
                    self.formattedItem["Items"].append(item_json)


            with open(resource_path("static/shop.bin"), "rb") as shopbar:
                binaryContent = bytearray(shopbar.read())

                byte0,byte1 = number_to_bytes(80+len(items_for_shop))
                binaryContent[10] = byte0
                binaryContent[11] = byte1

                byte0,byte1 = number_to_bytes(len(items_for_shop))

                # inventory 752
                binaryContent[754] = byte0
                binaryContent[755] = byte1
                byte0,byte1 = number_to_bytes(984)
                binaryContent[756] = byte0
                binaryContent[757] = byte1


                valid_start = bytes_to_number(binaryContent[12],binaryContent[13])
                for x in range(len(items_for_shop)):
                    product_index = 984+2*x
                    valid_item_index = valid_start + (60+x)*2
                    byte0,byte1 = number_to_bytes(items_for_shop[x][0])
                    binaryContent[product_index] = byte0
                    binaryContent[product_index+1] = byte1
                    binaryContent[valid_item_index] = byte0
                    binaryContent[valid_item_index+1] = byte1
                
                outZip.writestr("modified_shop.bin",binaryContent)

                ### code below prints out the shop information in relevant format

                # print(f"file type: {bytes_to_number(binaryContent[4],binaryContent[5])}")
                # shop_list_count = bytes_to_number(binaryContent[6],binaryContent[7])
                # print(f"shop list count: {shop_list_count}")
                # inventory_list_count = bytes_to_number(binaryContent[8],binaryContent[9])
                # print(f"inventory entry count: {inventory_list_count}")
                # product_list_count = bytes_to_number(binaryContent[10],binaryContent[11])
                # print(f"product entry count: {product_list_count}")
                # valid_start = bytes_to_number(binaryContent[12],binaryContent[13])
                # print(f"valid items offset: {valid_start}")
                
                # shop_start = 16
                # print("Shop Entries")
                # for x in range(shop_list_count):
                #     shop_index = shop_start+x*24
                #     print(f"---- Shop ID: {bytes_to_number(binaryContent[shop_index+18])}")
                #     print(f"---- Inventory Amount: {bytes_to_number(binaryContent[shop_index+16],binaryContent[shop_index+17])}")
                #     print(f"---- Inventory Offset: {bytes_to_number(binaryContent[shop_index+20],binaryContent[shop_index+21])}")
                #     print("----------")

                # inventory_start = shop_start+shop_list_count*24
                # print("Inventory Entries")
                # for x in range(inventory_list_count):
                #     inventory_index = inventory_start+x*8
                #     print(f"---- Inventory Address: {inventory_index}")
                #     print(f"---- Unlock event: {bytes_to_number(binaryContent[inventory_index],binaryContent[inventory_index+1])}")
                #     print(f"---- Product Amount: {bytes_to_number(binaryContent[inventory_index+2],binaryContent[inventory_index+3])}")
                #     print(f"---- Product Offset: {bytes_to_number(binaryContent[inventory_index+4],binaryContent[inventory_index+5])}")
                #     print("----------")

                # product_start = inventory_start+inventory_list_count*8
                # print("Product Entries")
                # for x in range(product_list_count):
                #     product_index = product_start+x*2
                #     print(f"---- Address {product_index}")
                #     print(f"---- Product (Item Id):  {bytes_to_number(binaryContent[product_index],binaryContent[product_index+1])}")

                # print("Valid Items")
                # for x in range(63):
                #     valid_index = valid_start+x*2
                #     item_id = bytes_to_number(binaryContent[valid_index],binaryContent[valid_index+1])
                #     if item_id!=0:
                #         print(f"---- Valid Item (Item Id):  {item_id}")

    def createSynthAssets(self, settings, randomizer, mod, outZip, pc_toggle):
        if locationType.SYNTH in settings.disabledLocations:
            return
        
        assignedSynth = self.getAssignmentSubsetFromType(randomizer.assignedItems,[locationType.SYNTH])

        synth_items = []
        for assignment in assignedSynth:
            synth_items.append(SynthLocation(assignment.location.LocationId,assignment.item.Id,[r for r in randomizer.synthesis_recipes if r.location==assignment.location][0]))

        # if locationType.Puzzle not in settings.disabledLocations:
        mod["assets"] += [modYml.getSynthMod(pc_toggle)]
        # assignedPuzzles = self.getAssignmentSubsetFromType(randomizer.assignedItems,[locationType.Puzzle])
        with open(resource_path("static/synthesis.bin"), "rb") as synthbar:
            binaryContent = bytearray(synthbar.read())
            for synth_loc in synth_items:

                starting_byte = synth_loc.getStartingLocation()
                data = synth_loc.getBytes()

                for iter,item in enumerate(data):
                    binaryContent[starting_byte+iter] = 0xFF & item
        
            outZip.writestr("modified_synth.bin",binaryContent)

        with open(resource_path("static/synthesis_reqs.bin"), "rb") as synthbar:
            binaryContent = bytearray(synthbar.read())

            # uncomment to see some data about the synth lists
            # index=16
            # while index+12<len(binaryContent):
            #     print(SynthList(index,binaryContent[index:]))
            #     index+=12

            # 3/6 free dev 8,9 bytes from offset index
            free_dev1 = number_to_bytes(3)
            free_dev2 = number_to_bytes(6)
            binaryContent[36] = free_dev1[0]
            binaryContent[37] = free_dev1[1]
            binaryContent[72] = free_dev2[0]
            binaryContent[73] = free_dev2[1]
            
            # 1,3 ori+ version, 
            # free_dev1 = number_to_bytes(1)
            # free_dev2 = number_to_bytes(3)
            # ori_plus_id = number_to_bytes(12) # not sure on this
            # binaryContent[33] = ori_plus_id[0]
            # binaryContent[35] = 0
            # binaryContent[36] = free_dev1[0]
            # binaryContent[37] = free_dev1[1]
            # binaryContent[69] = ori_plus_id[0]
            # binaryContent[71] = 0
            # binaryContent[72] = free_dev2[0]
            # binaryContent[73] = free_dev2[1]

            # uncomment to make all existing synth buyable conditions need 7 of that material
            # new_required_items = number_to_bytes(7)
            # start_index=376
            # for i in range(0,24):
            #     binaryContent[start_index+i*12+8] = new_required_items[0]
            #     binaryContent[start_index+i*12+9] = new_required_items[1]

            outZip.writestr("modified_synth_reqs.bin",binaryContent)

    def createChestVisualAssets(self, settings, randomizer, mod, outZip):
        if settings.chests_match_item:
            mod["assets"] += modYml.getChestVisualMod()
            chestList = KH2Chest.getChestList()
            treasures = self.getAssignmentSubset(randomizer.assignedItems,[locationCategory.CHEST])
            treasures = [trsr for trsr in treasures 
                         if locationType.Puzzle not in trsr.location.LocationTypes 
                         and locationType.Critical not in trsr.location.LocationTypes 
                         and locationType.SYNTH not in trsr.location.LocationTypes]
            for trsr in treasures:
                #i dunno just in case i guess because D/G starting items are labled as free and chests
                if locationType.Free in trsr.location.LocationTypes and trsr.location.LocationId in range(1,3):
                    #print('party stating item?')
                    continue
                if trsr.location.LocationId == "315" and trsr.item.ItemType in [itemType.PROOF_OF_CONNECTION, itemType.PROOF_OF_PEACE, itemType.PROOF, itemType.PROMISE_CHARM]:
                    # if this chest in STT Station of Serenity is a proof, it can't be big since it's a tutorial chest
                    continue
                #use location id to get chest index and name
                chest = chestList[trsr.location.LocationId]
                chestTypeId = getChestVisualId(trsr.location.LocationTypes, trsr.item.ItemType)
                #open and write file
                try: #open yml first if it exists
                    spawnFile = yaml.safe_load(open(resource_path('static/chests/ard/'+chest.SpawnName+'.yml')))
                except: #open spawn if yml doesn't
                    spawnFile = yaml.safe_load(open(resource_path('static/chests/ard/'+chest.SpawnName+'.spawn')))
                finally: #edit and save yml
                    spawnFile[0]["Entities"][chest.ChestIndex]["ObjectId"] = chestTypeId
                    yaml.dump(spawnFile,open(resource_path('static/chests/ard/'+chest.SpawnName+'.yml'),"w"), default_flow_style=False)
            #filelist huge so get list from the chest class
            fileList = getChestFileList()
            #Ards
            for path in fileList:
                outZip.write(resource_path('static/chests/ard/'+path+'.yml'), "chest/ard/"+path+'.yml')
            #Remasterd Textures
            outZip.write(resource_path('static/chests/remastered/trash.dds'), 'chest/remastered/trash.dds')
            outZip.write(resource_path('static/chests/remastered/abilities.dds'), 'chest/remastered/abilities.dds')
            outZip.write(resource_path('static/chests/remastered/forms.dds'), 'chest/remastered/forms.dds')
            outZip.write(resource_path('static/chests/remastered/magic.dds'), 'chest/remastered/magic.dds')
            outZip.write(resource_path('static/chests/remastered/pages.dds'), 'chest/remastered/pages.dds')
            outZip.write(resource_path('static/chests/remastered/reports.dds'), 'chest/remastered/reports.dds')
            outZip.write(resource_path('static/chests/remastered/stats.dds'), 'chest/remastered/stats.dds')
            outZip.write(resource_path('static/chests/remastered/summons.dds'), 'chest/remastered/summons.dds')
            outZip.write(resource_path('static/chests/remastered/unlocks.dds'), 'chest/remastered/unlocks.dds')
            outZip.write(resource_path('static/chests/remastered/weapons.dds'), 'chest/remastered/weapons.dds')
            outZip.write(resource_path('static/chests/remastered/proofs_glow.dds'), 'chest/remastered/proofs_glow.dds')
            outZip.write(resource_path('static/chests/remastered/proofs.dds'), 'chest/remastered/proofs.dds')
            #Listpatch
            outZip.write(resource_path('static/chests/ChestObjList.script'), 'chest/ChestObjList.yml')
            #MSET
            outZip.write(resource_path('static/chests/obj/F_EX030_LK.mset'), 'chest/obj/F_EX030_LK.mset')
            outZip.write(resource_path('static/chests/obj/F_EX040_LK.mset'), 'chest/obj/F_EX040_LK.mset')
            outZip.write(resource_path('static/chests/obj/F_EX040_RX.mset'), 'chest/obj/F_EX040_RX.mset')
            #MDLX
            outZip.write(resource_path('static/chests/obj/F_EX030_JNK.mdlx'), 'chest/obj/F_EX030_JNK.mdlx')
            outZip.write(resource_path('static/chests/obj/F_EX030_ABL.mdlx'), 'chest/obj/F_EX030_ABL.mdlx')
            outZip.write(resource_path('static/chests/obj/F_EX030_FRM.mdlx'), 'chest/obj/F_EX030_FRM.mdlx')
            outZip.write(resource_path('static/chests/obj/F_EX030_MAG.mdlx'), 'chest/obj/F_EX030_MAG.mdlx')
            outZip.write(resource_path('static/chests/obj/F_EX030_PAG.mdlx'), 'chest/obj/F_EX030_PAG.mdlx')
            outZip.write(resource_path('static/chests/obj/F_EX030_REP.mdlx'), 'chest/obj/F_EX030_REP.mdlx')
            outZip.write(resource_path('static/chests/obj/F_EX030_STA.mdlx'), 'chest/obj/F_EX030_STA.mdlx')
            outZip.write(resource_path('static/chests/obj/F_EX030_SMN.mdlx'), 'chest/obj/F_EX030_SMN.mdlx')
            outZip.write(resource_path('static/chests/obj/F_EX030_VST.mdlx'), 'chest/obj/F_EX030_VST.mdlx')
            outZip.write(resource_path('static/chests/obj/F_EX030_WEP.mdlx'), 'chest/obj/F_EX030_WEP.mdlx')
            outZip.write(resource_path('static/chests/obj/F_EX040_PRF.mdlx'), 'chest/obj/F_EX040_PRF.mdlx')

    @staticmethod
    def write_music_replacements(replacements: dict[str, str], outZip):
        if len(replacements) > 0:
            music_replacements_string = ''
            for original, replacement in replacements.items():
                music_replacements_string += '[{}] was replaced by [{}]\n'.format(original, replacement)
            outZip.writestr('music-replacement-list.txt', music_replacements_string)

    def assignStartingItems(self, settings, randomizer):
        def padItems(itemList):
            while(len(itemList)<32):
                itemList.append(0)

        masterItemList = Items.getItemList() + Items.getActionAbilityList() + Items.getSupportAbilityList() + [Items.getTT1Jailbreak()] + [Items.getPromiseCharm()]
        reports = [i.Id for i in masterItemList if i.ItemType==itemType.REPORT]
        story_unlocks = [i.Id for i in masterItemList if i.ItemType==itemType.STORYUNLOCK]
        donald_goofy_handled_items = reports+story_unlocks
        sora_abilities = [i.Id for i in masterItemList if (i.ItemType==itemType.GROWTH_ABILITY or i.ItemType==itemType.ACTION_ABILITY or i.ItemType==itemType.SUPPORT_ABILITY)]

        riku_handled = [i.Id for i in masterItemList if i.Id not in donald_goofy_handled_items and i.Id not in sora_abilities]

        donaldStartingItems = [1+0x8000,3+0x8000]+[l.item.Id for l in self.getAssignmentSubsetFromType(randomizer.assignedDonaldItems,[locationType.Free])] + [i for i in settings.startingItems if i in reports]
        padItems(donaldStartingItems)
        self.formattedPlrp.append({
            "Character": 2, # Donald Starting Items
            "Id": 0,
            "Hp": 20,
            "Mp": 100,
            "Ap": settings.donald_ap-5,
            "ArmorSlotMax": 1,
            "AccessorySlotMax": 2,
            "ItemSlotMax": 2,
            "Items": donaldStartingItems,
            "Padding": [0] * 52
        })

        goofyStartingItems = [1+0x8000,1+0x8000,1+0x8000,]+[l.item.Id for l in self.getAssignmentSubsetFromType(randomizer.assignedGoofyItems,[locationType.Free])] + [i for i in settings.startingItems if i in story_unlocks]
        padItems(goofyStartingItems)
        self.formattedPlrp.append({
            "Character": 3, # Goofy Starting Items
            "Id": 0,
            "Hp": 20,
            "Mp": 100,
            "Ap": settings.goofy_ap-4,
            "ArmorSlotMax": 2,
            "AccessorySlotMax": 1,
            "ItemSlotMax": 3,
            "Items": goofyStartingItems,
            "Padding": [0] * 52
        })

        rikuStartingItems = [i+0x8000 for i in [1,1,1,1,3,3,438,436,187,208,411,422,414,415,416]] + [417,419] + [i for i in settings.startingItems if i in riku_handled]
        padItems(rikuStartingItems)
        self.formattedPlrp.append({
            "Character": 13, # Riku Starting Items
            "Id": 0,
            "Hp": 20,
            "Mp": 100,
            "Ap": settings.goofy_ap-4,
            "ArmorSlotMax": 2,
            "AccessorySlotMax": 1,
            "ItemSlotMax": 6,
            "Items": rikuStartingItems,
            "Padding": [0] * 52
        })

        ability_equip = 0x8000 if settings.auto_equip_abilities else 0

        soraStartingItems = [l.item.Id for l in self.getAssignmentSubsetFromType(randomizer.assignedItems,[locationType.Critical])] + \
                            [i+ability_equip for i in settings.startingItems if i in sora_abilities]
        padItems(soraStartingItems)
        self.formattedPlrp.append({
            "Character": 1, # Sora Starting Items (Crit)
            "Id": 7, # crit difficulty
            "Hp": 20,
            "Mp": 100,
            "Ap": settings.sora_ap,
            "ArmorSlotMax": 1,
            "AccessorySlotMax": 1,
            "ItemSlotMax": 3,
            "Items": soraStartingItems[:7],
            "Padding": [0] * 52
        })

        lionSoraItems = [32930, 32930, 32931, 32931, 33288, 33289, 33290, 33294]
        padItems(lionSoraItems)
        self.formattedPlrp.append({
            "Character": 135, # Lion Dash on Lion Sora
            "Id": 0,
            "Hp": 0,
            "Mp": 0,
            "Ap": 0,
            "ArmorSlotMax": 0,
            "AccessorySlotMax": 0,
            "ItemSlotMax": 0,
            "Items": lionSoraItems,
            "Padding": [0] * 52
        })
        
        self.formattedPlrp.append({
            "Character": 1, # Sora Starting Items (Non Crit)
            "Id": 0,
            "Hp": 20,
            "Mp": 100,
            "Ap": settings.sora_ap,
            "ArmorSlotMax": 1,
            "AccessorySlotMax": 1,
            "ItemSlotMax": 3,
            "Items": soraStartingItems[7:],
            "Padding": [0] * 52
        })


    def assignWeaponStats(self, randomizer):
        weapons = self.getAssignmentSubset(randomizer.assignedItems,[locationCategory.WEAPONSLOT]) + \
            self.getAssignmentSubset(randomizer.assignedDonaldItems,[locationCategory.WEAPONSLOT]) + \
            self.getAssignmentSubset(randomizer.assignedGoofyItems,[locationCategory.WEAPONSLOT])
        
        for weapon in weapons:
            weaponStats = [stat for stat in randomizer.weaponStats if stat.location==weapon.location][0]
            self.formattedItem["Stats"].append({
                "Id": weapon.location.LocationId,
                "Attack": weaponStats.strength,
                "Magic": weaponStats.magic,
                "Defense": 0,
                "Ability": weapon.item.Id,
                "AbilityPoints": 0,
                "Unknown08": 100,
                "FireResistance": 100,
                "IceResistance": 100,
                "LightningResistance": 100,
                "DarkResistance": 100,
                "Unknown0d": 100,
                "GeneralResistance": 100,
                "Unknown": 0
            })




    def assignFormLevels(self, randomizer):
        formDict = {0:"Summon", 1:"Valor",2:"Wisdom",3:"Limit",4:"Master",5:"Final"}
        for index,levelType in enumerate([locationCategory.SUMMONLEVEL,locationCategory.VALORLEVEL,locationCategory.WISDOMLEVEL,locationCategory.LIMITLEVEL,locationCategory.MASTERLEVEL,locationCategory.FINALLEVEL]):
            levels = self.getAssignmentSubset(randomizer.assignedItems,[levelType])
            formName = formDict[index]
            self.formattedFmlv[formName] = []
            for level_number in range(1,8):
                for lvl in levels:
                    if lvl.location.LocationId == level_number:
                        formExp = [l for l in randomizer.formLevelExp if l == lvl.location][0]
                        self.formattedFmlv[formName].append({
                            "Ability": lvl.item.Id if index!=0 else 0, # making summon junk items zero
                            "Experience": formExp.experience,
                            "FormId": index,
                            "FormLevel": lvl.location.LocationId,
                            "GrowthAbilityLevel": 0,
                        })

    def assignGoofyBonuses(self, randomizer):
        goofyBonuses = self.getAssignmentSubset(randomizer.assignedGoofyItems,[locationCategory.DOUBLEBONUS,locationCategory.HYBRIDBONUS,locationCategory.ITEMBONUS,locationCategory.STATBONUS])
        for bon in goofyBonuses:
            if not bon.location.LocationId in self.formattedBons.keys():
                self.formattedBons[bon.location.LocationId] = {}
            charId = 3 # Goofy id
            charName = "Goofy"
            item1 = 0
            item2 = 0
            item1 = bon.item.Id
            if bon.item2 is not None:
                item2 = bon.item2.Id
            self.formattedBons[bon.location.LocationId][charName] = {
                "RewardId": bon.location.LocationId,
                "CharacterId": charId,
                "HpIncrease": 0,
                "MpIncrease": 0,
                "DriveGaugeUpgrade": 0,
                "ItemSlotUpgrade": 0,
                "AccessorySlotUpgrade": 0,
                "ArmorSlotUpgrade": 0,
                "BonusItem1": item1,
                "BonusItem2": item2,
                "Padding": 0
            }

    def assignDonaldBonuses(self, randomizer):
        donaldBonuses = self.getAssignmentSubset(randomizer.assignedDonaldItems,[locationCategory.DOUBLEBONUS,locationCategory.HYBRIDBONUS,locationCategory.ITEMBONUS,locationCategory.STATBONUS])
        for bon in donaldBonuses:
            if not bon.location.LocationId in self.formattedBons.keys():
                self.formattedBons[bon.location.LocationId] = {}
            charId = 2 # Donald id
            charName = "Donald"
            item1 = 0
            item2 = 0
            item1 = bon.item.Id
            if bon.item2 is not None:
                item2 = bon.item2.Id
            self.formattedBons[bon.location.LocationId][charName] = {
                "RewardId": bon.location.LocationId,
                "CharacterId": charId,
                "HpIncrease": 0,
                "MpIncrease": 0,
                "DriveGaugeUpgrade": 0,
                "ItemSlotUpgrade": 0,
                "AccessorySlotUpgrade": 0,
                "ArmorSlotUpgrade": 0,
                "BonusItem1": item1,
                "BonusItem2": item2,
                "Padding": 0
            }

    def assignSoraBonuses(self, randomizer):
        soraBonuses = self.getAssignmentSubset(randomizer.assignedItems,[locationCategory.DOUBLEBONUS,locationCategory.HYBRIDBONUS,locationCategory.ITEMBONUS,locationCategory.STATBONUS])
        for bon in soraBonuses:
            if not bon.location.LocationId in self.formattedBons.keys():
                self.formattedBons[bon.location.LocationId] = {}
            charId = 1 # Sora id
            charName = "Sora"
            if locationType.STT in bon.location.LocationTypes:
                charId = 14 # roxas id
                charName = "Roxas"

            #determine if assigned item is a stat bonus, and if so, use the bonuses native stat update
            hpIncrease = 0
            mpIncrease = 0
            driveIncrease = 0
            itemIncrease = 0
            accessoryIncrease = 0
            armorIncrease = 0
            item1 = 0
            item2 = 0
            if bon.item.ItemType == itemType.SLOT or bon.item.ItemType == itemType.GAUGE:
                if bon.item.Id == 470: # HP increase
                    hpIncrease+=5
                if bon.item.Id == 471: # MP increase
                    mpIncrease+=10
                if bon.item.Id == 472: # Drive increase
                    driveIncrease+=1
                if bon.item.Id == 473: # Armor increase
                    armorIncrease+=1
                if bon.item.Id == 474: # Accessory increase
                    accessoryIncrease+=1
                if bon.item.Id == 463: # Item increase
                    itemIncrease+=1
            else:
                item1 = bon.item.Id
            if bon.item2 is not None and (bon.item2.ItemType==itemType.SLOT or bon.item2.ItemType == itemType.GAUGE):
                if bon.item2.Id == 470: # HP increase
                    hpIncrease+=5
                if bon.item2.Id == 471: # MP increase
                    mpIncrease+=10
                if bon.item2.Id == 472: # Drive increase
                    driveIncrease+=1
                if bon.item2.Id == 473: # Armor increase
                    armorIncrease+=1
                if bon.item2.Id == 474: # Accessory increase
                    accessoryIncrease+=1
                if bon.item2.Id == 463: # Item increase
                    itemIncrease+=1
            elif bon.item2 is not None:
                item2 = bon.item2.Id


            self.formattedBons[bon.location.LocationId][charName] = {
                "RewardId": bon.location.LocationId,
                "CharacterId": charId,
                "HpIncrease": hpIncrease,
                "MpIncrease": mpIncrease,
                "DriveGaugeUpgrade": driveIncrease,
                "ItemSlotUpgrade": itemIncrease,
                "AccessorySlotUpgrade": accessoryIncrease,
                "ArmorSlotUpgrade": armorIncrease,
                "BonusItem1": item1,
                "BonusItem2": item2,
                "Padding": 0
            }



    def assignLevels(self, settings: RandomizerSettings, randomizer):
        levels = self.getAssignmentSubset(randomizer.assignedItems,[locationCategory.LEVEL])

        # get the triple of items for each level
        items_for_sword_level = {}
        offsets = DreamWeaponOffsets()
        for sword_level in range(1,100):
            sword_item = 0
            shield_item = 0
            staff_item = 0
            shield_level = offsets.get_item_lookup_for_shield(settings.level_checks,sword_level) if settings.split_levels else sword_level
            staff_level = offsets.get_item_lookup_for_staff(settings.level_checks,sword_level) if settings.split_levels else sword_level
            for lvup in levels:
                if lvup.location.LocationId == sword_level:
                    sword_item = lvup.item.Id
                if lvup.location.LocationId == shield_level:
                    shield_item = lvup.item.Id
                if lvup.location.LocationId == staff_level:
                    staff_item = lvup.item.Id
            items_for_sword_level[sword_level] = (sword_item,shield_item,staff_item)


        for lvup in levels:
            levelStats = [lv for lv in randomizer.levelStats if lv.location==lvup.location][0]
            item_id = items_for_sword_level[lvup.location.LocationId]
            self.formattedLvup["Sora"][lvup.location.LocationId] = {
                "Exp": levelStats.experience,
                "Strength": levelStats.strength,
                "Magic": levelStats.magic,
                "Defense": levelStats.defense,
                "Ap": levelStats.ap,
                "SwordAbility": item_id[0],
                "ShieldAbility": item_id[1],
                "StaffAbility": item_id[2],
                "Padding": 0,
                "Character": "Sora",
                "Level": lvup.location.LocationId
            }



    def assignTreasures(self, randomizer):
        treasures = self.getAssignmentSubset(randomizer.assignedItems,[locationCategory.POPUP,locationCategory.CHEST])
        treasures = [trsr for trsr in treasures if locationType.Puzzle not in trsr.location.LocationTypes and locationType.Critical not in trsr.location.LocationTypes and locationType.SYNTH not in trsr.location.LocationTypes]

        for trsr in treasures:
            self.formattedTrsr[trsr.location.LocationId] = {"ItemId":trsr.item.Id}

    def getAssignmentSubset(self,assigned,categories : list[locationCategory]):
        return [assignment for assignment in assigned if any(item is assignment.location.LocationCategory for item in categories)]

    def getAssignmentSubsetFromType(self,assigned,types):
        return [assignment for assignment in assigned if any(item in assignment.location.LocationTypes for item in types)]


class CosmeticsOnlyZip:

    def __init__(self, ui_settings: SeedSettings, extra_data: ExtraConfigurationData):
        self.settings = ui_settings
        self.extra_data = extra_data
        self.output_zip: Optional[io.BytesIO] = None
        self.create_zip()

    def create_zip(self):
        data = io.BytesIO()
        with zipfile.ZipFile(data, "w", zipfile.ZIP_DEFLATED) as out_zip:
            mod = {
                "title": "Randomized Cosmetics",
                "description": "Generated by the KH2 Randomizer Seed Generator.",
                "assets": []
            }

            mod["assets"].extend(commandmenu.randomize_command_menus(self.extra_data.command_menu_choice))

            music_assets, music_replacements = CosmeticsMod.randomize_music(self.settings)
            mod["assets"].extend(music_assets)
            SeedZip.write_music_replacements(music_replacements, out_zip)

            out_zip.writestr("mod.yml", yaml.dump(mod, line_break="\r\n"))

            out_zip.write(resource_path("static/icons/misc/Kingdom Hearts II.png"), "icon.png")

        data.seek(0)
        self.output_zip = data


class BossEnemyOnlyZip:

    def __init__(self, seed_name: str, ui_settings: SeedSettings, platform: bool):
        self.settings = ui_settings
        self.enemy_options = makeKHBRSettings(seed_name,self.settings)
        self.platform = platform
        self.output_zip: Optional[io.BytesIO] = None
        self.create_zip()

    def create_zip(self):
        data = io.BytesIO()
        with zipfile.ZipFile(data, "w", zipfile.ZIP_DEFLATED) as out_zip:
            mod = {
                "title": "Randomized Bosses/Enemies",
                "description": "Generated by the KH2 Randomizer Seed Generator.",
                "assets": []
            }            
            
            pc_seed_toggle = (self.platform=="PC")

            def _shouldRunKHBR():
                if not self.enemy_options.get("boss", False) in [False, "Disabled"]:
                    return True
                if not self.enemy_options.get("enemy", False) in [False, "Disabled"]:
                    return True
                
                return False

            enemySpoilers = None
            enemySpoilersJSON = {}
            if _shouldRunKHBR():
                enemySpoilers = None
                enemySpoilersJSON = {}
            
                if pc_seed_toggle:
                    self.enemy_options["memory_expansion"] = True
                else:
                    self.enemy_options["memory_expansion"] = False
                
                enemySpoilers = invoke_khbr(self.enemy_options, mod, out_zip)

                lines = enemySpoilers.split("\n")

                current_key = ""
                for line in lines:
                    if '\t' in line:
                        modded_line = line.replace('\t','')
                        enemies = modded_line.split(" became ")
                        # this is adding to the current list
                        new_entry = {}
                        new_entry["original"] = enemies[0]
                        new_entry["new"] = enemies[1]
                        enemySpoilersJSON[current_key].append(new_entry)
                    elif line!="":
                        current_key = line
                        enemySpoilersJSON[current_key] = []
                if enemySpoilersJSON:
                    out_zip.writestr("enemies.rando", base64.b64encode(json.dumps(enemySpoilersJSON).encode('utf-8')).decode('utf-8'))
                    # for boss_replacement in enemySpoilersJSON["BOSSES"]:
                    #     print(f"{boss_replacement['original']} {boss_replacement['new']}")

            else:
                raise GeneratorException("Trying to generate boss/enemy only mod without enabling those settings.")

            print("Passed boss/enemy")

            out_zip.writestr("mod.yml", yaml.dump(mod, line_break="\r\n"))
            out_zip.write(resource_path("static/icons/misc/Kingdom Hearts II.png"), "icon.png")
            out_zip.writestr("enemyspoilers.txt", enemySpoilers)

        data.seek(0)
        self.output_zip = data