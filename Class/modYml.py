class modYml:
    retryDarkThorn = "retryDarkThorn"
    retryDataXemnas = "retryDataXemnas"

    def getDefaultMod():
        return {
            "title": "Randomizer Seed",
            "assets": [
                {
                    "name": "msg/jp/sys.bar",
                    "multi": [
                        {
                            "name": "msg/us/sys.bar"
                        },
                        {
                            "name": "msg/uk/sys.bar"
                        }
                    ],
                    "method": "binarc",
                    "source": [
                        {
                            "name": "sys",
                            "type": "list",
                            "method": "kh2msg",
                            "source": [
                                {
                                    "name": "sys.yml",
                                    "language": "en"
                                }
                            ]
                        }
                    ]
                },
                {
                    "name": "msg/jp/jm.bar",
                    "multi": [
                        {
                            "name": "msg/us/jm.bar"
                        },
                        {
                            "name": "msg/uk/jm.bar"
                        }
                    ],
                    "method": "binarc",
                    "source": [
                        {
                            "name": "jm",
                            "type": "list",
                            "method": "kh2msg",
                            "source": [
                                {
                                    "name": "jm.yml",
                                    "language": "en"
                                }
                            ]
                        }
                    ]
                },
                {
                    "name": "00battle.bin",
                    "method": "binarc",
                    "source": [
                        {
                            "name": "fmlv",
                            "method": "listpatch",
                            "type": "List",
                            "source": [
                                {
                                    "name": "FmlvList.yml",
                                    "type": "fmlv"
                                }
                            ]
                        },
                        {
                            "name": "lvup",
                            "method": "listpatch",
                            "type": "List",
                            "source": [
                                {
                                    "name": "LvupList.yml",
                                    "type": "lvup"
                                }
                            ]
                        },
                        {
                            "name": "bons",
                            "method": "listpatch",
                            "type": "List",
                            "source": [
                                {
                                    "name": "BonsList.yml",
                                    "type": "bons"
                                }
                            ]
                        },
                        {
                            "name": "plrp",
                            "method": "listpatch",
                            "type": "List",
                            "source": [
                                {
                                    "name": "PlrpList.yml",
                                    "type": "plrp"
                                }
                            ]
                        }
                    ]
                },
                {
                    "name": "03system.bin",
                    "method": "binarc",
                    "source": [
                        {
                            "name": "trsr",
                            "method": "listpatch",
                            "type": "List",
                            "source": [
                                {
                                    "name": "TrsrList.yml",
                                    "type": "trsr"
                                }
                            ]
                        },
                        {
                            "name": "item",
                            "method": "listpatch",
                            "type": "List",
                            "source": [
                                {
                                    "name": "ItemList.yml",
                                    "type": "item"
                                }
                            ]
                        }
                    ]
                }
            ]
        }

    def getJMYAML():
        return [
            {
                "id": 20279,
                "en": "Defeat Xemnas at the top of the Castle"
            },
            {
                "id": 20280,
                "en": "Defeat Storm Rider"
            },
            {
                "id": 20281,
                "en": "Defeat Xaldin in the Courtyard"
            },
            {
                "id": 20282,
                "en": "Defeat Dr. Finkelstein's Experiment"
            },
            {
                "id": 20283,
                "en": "Defeat Genie Jafar"
            },
            {
                "id": 20284,
                "en": "Defeat Hades"
            },
            {
                "id": 20285,
                "en": "Defeat Groundshaker"
            },
            {
                "id": 20286,
                "en": "Fight alongside Axel in the world Between"
            },
            {
                "id": 20287,
                "en": "Defend Hollow Bastion from the Heartless Army"
            },
            {
                "id": 20288,
                "en": "Defeat Grim Reaper II"
            },
            {
                "id": 20289,
                "en": "Protect the Cornerstone of Light from Pete"
            },
            {
                "id": 20290,
                "en": "Defeat the Master Control Program"
            },
            {
                "id": 20291,
                "en": "Confront DiZ in the Mansion's Pod Room"
            }
        ]

    def getSysYAML(seedHashIcons, crit_mode = False):
        seedHashString = " ".join(["{:icon " + icon + "}" for icon in seedHashIcons])
        sys = [{"id": 17198, "en":seedHashString}]
        sys.append({"id": 19482, "en": "Important Checks Found"})
        if crit_mode:
            sys.append({"id": 17201, "en": "{:color #FF000080}Beginner (WARNING)"})
            sys.append({"id": 17202, "en": "{:color #FF000080}Standard (WARNING)"})
            sys.append({"id": 17203, "en": "{:color #FF000080}Proud (WARNING)"})
            sys.append({
                "id": 17204,
                "en": "An easier mode for beginners.\n{:color #FF000080}Critical Bonuses are turned on. The seven\nrandom starting items will be unobtainable."
            })
            sys.append({
                "id": 17205,
                "en": "A balanced mode best for those challenging\nthis game for the first time.\n{:color #FF000080}Critical Bonuses are turned on. The seven\nrandom starting items will be unobtainable."
            })
            sys.append({
                "id": 17206,
                "en": "A difficult mode with stronger enemies.\nBest for those seeking a challenge.\n{:color #FF000080}Critical Bonuses are turned on. The seven\nrandom starting items will be unobtainable."
            })
            sys.append({
                "id": 20020,
                "en": "A true test of skill for the adept. Begin\nwith certain abilities and other perks.\n{:color #F0F00080}Critical Bonuses are turned on. The seven\nstarting items have been randomized."
            })
        else:
            sys.append({
                "id": 20020,
                "en": "A true test of skill for the adept. Begin\nwith certain abilities and other perks.\n{:color #F0F00080}Critical Bonuses are turned off. The seven\nstarting items will be junk."
            })

        return sys
    
    def getASDataMod():
        return [{"name": "ard/hb32.ard","multi": [{"name": "ard/us/hb32.ard"}],"method":"binarc","source":[{"name":"evt","type":"areadatascript","method":"areadatascript","source":[{"name":"asdata/hb32evt.script"}]}] },
                {"name": "ard/hb33.ard","multi": [{"name": "ard/us/hb33.ard"}],"method":"binarc","source":[{"name":"evt","type":"areadatascript","method":"areadatascript","source":[{"name":"asdata/hb33evt.script"}]}] },
                {"name": "ard/hb34.ard","multi": [{"name": "ard/us/hb34.ard"}],"method":"binarc","source":[{"name":"evt","type":"areadatascript","method":"areadatascript","source":[{"name":"asdata/hb34evt.script"}]}] },
                {"name": "ard/hb38.ard","multi": [{"name": "ard/us/hb38.ard"}],"method":"binarc","source":[{"name":"evt","type":"areadatascript","method":"areadatascript","source":[{"name":"asdata/hb38evt.script"}]}] }]

    def getPuzzleMod():
        return {
                    "name": "menu/jp/jiminy.bar",
                    "multi": [
                        {
                            "name": "menu/us/jiminy.bar"
                        },
                        {
                            "name": "menu/uk/jiminy.bar"
                        },
                        {
                            "name": "menu/fm/jiminy.bar"
                        }
                    ],
                    "method": "binarc",
                    "source": [
                        {
                            "name": "puzz",
                            "type": "jimidata",
                            "method": "copy",
                            "source": [
                                {
                                    "name": "modified_puzzle.bin"
                                }
                            ]
                        }
                    ]
                }
    def getSynthMod():
        return {
                    "name": "menu/jp/mixdata.bar",
                    "multi": [
                        {
                            "name": "menu/us/mixdata.bar"
                        },
                        {
                            "name": "menu/uk/mixdata.bar"
                        },
                        {
                            "name": "menu/fm/mixdata.bar"
                        }
                    ],
                    "method": "binarc",
                    "source": [
                        {
                            "name": "reci",
                            "type": "synthesis",
                            "method": "copy",
                            "source": [
                                {
                                    "name": "modified_synth.bin"
                                }
                            ]
                        },
                        {
                            "name": "cond",
                            "type": "synthesis",
                            "method": "copy",
                            "source": [
                                {
                                    "name": "modified_synth_reqs.bin"
                                }
                            ]
                        }
                    ]
                }
    def getSkipCarpetEscapeMod():
        return {
                "name": "ard/al11.ard",
                "multi": [
                    {
                        "name": "ard/us/al11.ard"
                    },
                    {
                        "name": "ard/fr/al11.ard"
                    },
                    {
                        "name": "ard/gr/al11.ard"
                    },
                    {
                        "name": "ard/it/al11.ard"
                    },
                    {
                        "name": "ard/sp/al11.ard"
                    }
                ],
                "method": "binarc",
                "source": [
                    {
                        "name": "evt",
                        "type": "areadatascript",
                        "method": "areadatascript",
                        "source": [
                            {
                                "name": "skip_carpet_escape.script"
                            }
                        ]
                    }
                ]
            }

    def getMapSkipMod():
        return [{
                "name": "msg/us/ca.bar",
                "method": "binarc",
                "source": [
                    {
                        "name": "ca",
                        "type": "list",
                        "method": "kh2msg",
                        "source": [
                            {
                                "name": "map_skip/ca.yml",
                                "language": "en"
                            }
                        ]
                    }
                ]
               },{
                "name": "libretto-ca.bar",
                "method": "copy",
                "source": [
                    {
                        "name": "map_skip/libretto-ca.bar",
                    }
                ]
               },]



    def getRetryMod(mod_choice):
        mod_names = {}
        mod_names[modYml.retryDarkThorn] = ("BB05_MS104B.bar","BB05","retry_dark_thorn.bin")
        mod_names[modYml.retryDataXemnas] = ("EH20_MS113_RE.bar","EH20","retry_data_xemnas.bin")
        return {
                    "name": "msn/jp/"+mod_names[mod_choice][0],
                    "multi": [
                        {
                            "name": "msn/us/"+mod_names[mod_choice][0]
                        },
                        {
                            "name": "msn/fr/"+mod_names[mod_choice][0]
                        },
                        {
                            "name": "msn/gr/"+mod_names[mod_choice][0]
                        },
                        {
                            "name": "msn/it/"+mod_names[mod_choice][0]
                        },
                        {
                            "name": "msn/sp/"+mod_names[mod_choice][0]
                        }
                    ],
                    "method": "binarc",
                    "source": [
                        {
                            "name": mod_names[mod_choice][1],
                            "type": "list",
                            "method": "copy",
                            "source": [
                                {
                                    "name": mod_names[mod_choice][2]
                                }
                            ]
                        }
                    ]
                }

    def getBetterSTTMod(boss_enemy_enabled):
        return [{"name": "limit/fm/trinity_zz.bar","multi":[{"name":"limit/us/trinity_zz.bar"},{"name":"limit/fr/trinity_zz.bar"},{"name":"limit/gr/trinity_zz.bar"},{"name":"limit/it/trinity_zz.bar"},{"name":"limit/sp/trinity_zz.bar"}],"method": "copy","source": [{"name": "better_stt/trinity_zz.bar"}]},
                {"name": "obj/B_EX100.mset","method": "copy","source": [{"name": "better_stt/B_EX100.mset"}]},
                {"name": "obj/F_TT010.mset","method": "copy","source": [{"name": "better_stt/F_TT010.mset"}]},
                {"name": "obj/P_EX110.mset","method": "copy","source": [{"name": "better_stt/P_EX110.mset"}]},
                {"name": "00objentry.bin","method": "listpatch","type": "List","source": [{"name": "better_stt/ObjList_Better_STT.yml", "type": "objentry"}]},
                {"name": "obj/W_EX010_RX.mset","method": "copy","source": [{"name": "better_stt/W_EX010_RX.mset"}]},] + \
                ([{"name": "obj/B_EX100_SR.mset","method": "copy","source": [{"name": "better_stt/B_EX100_SR.mset"}]},] if boss_enemy_enabled else []),[{"method":"copy", "name":"cmd", "type":"list", "source":[{"name":"better_stt/cmd.list"}]}]

