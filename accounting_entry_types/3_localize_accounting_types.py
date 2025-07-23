#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import glob
import re
from collections import defaultdict

# 从wallet_journal_ref.py中提取的ref_type与id的映射关系
ref_type_to_id = {
    "player_trading": 1,
    "market_transaction": 2,
    "gm_cash_transfer": 3,
    "mission_reward": 7,
    "clone_activation": 8,
    "inheritance": 9,
    "player_donation": 10,
    "corporation_payment": 11,
    "docking_fee": 12,
    "office_rental_fee": 13,
    "factory_slot_rental_fee": 14,
    "repair_bill": 15,
    "bounty": 16,
    "bounty_prize": 17,
    "insurance": 19,
    "mission_expiration": 20,
    "mission_completion": 21,
    "shares": 22,
    "courier_mission_escrow": 23,
    "mission_cost": 24,
    "agent_miscellaneous": 25,
    "lp_store": 26,
    "agent_location_services": 27,
    "agent_donation": 28,
    "agent_security_services": 29,
    "agent_mission_collateral_paid": 30,
    "agent_mission_collateral_refunded": 31,
    "agents_preward": 32,
    "agent_mission_reward": 33,
    "agent_mission_time_bonus_reward": 34,
    "cspa": 35,
    "cspaofflinerefund": 36,
    "corporation_account_withdrawal": 37,
    "corporation_dividend_payment": 38,
    "corporation_registration_fee": 39,
    "corporation_logo_change_cost": 40,
    "release_of_impounded_property": 41,
    "market_escrow": 42,
    "agent_services_rendered": 43,
    "market_fine_paid": 44,
    "corporation_liquidation": 45,
    "brokers_fee": 46,
    "corporation_bulk_payment": 47,
    "alliance_registration_fee": 48,
    "war_fee": 49,
    "alliance_maintainance_fee": 50,
    "contraband_fine": 51,
    "clone_transfer": 52,
    "acceleration_gate_fee": 53,
    "transaction_tax": 54,
    "jump_clone_installation_fee": 55,
    "manufacturing": 56,
    "researching_technology": 57,
    "researching_time_productivity": 58,
    "researching_material_productivity": 59,
    "copying": 60,
    "reverse_engineering": 62,
    "contract_auction_bid": 63,
    "contract_auction_bid_refund": 64,
    "contract_collateral": 65,
    "contract_reward_refund": 66,
    "contract_auction_sold": 67,
    "contract_reward": 68,
    "contract_collateral_refund": 69,
    "contract_collateral_payout": 70,
    "contract_price": 71,
    "contract_brokers_fee": 72,
    "contract_sales_tax": 73,
    "contract_deposit": 74,
    "contract_deposit_sales_tax": 75,
    "contract_auction_bid_corp": 77,
    "contract_collateral_deposited_corp": 78,
    "contract_price_payment_corp": 79,
    "contract_brokers_fee_corp": 80,
    "contract_deposit_corp": 81,
    "contract_deposit_refund": 82,
    "contract_reward_deposited": 83,
    "contract_reward_deposited_corp": 84,
    "bounty_prizes": 85,
    "advertisement_listing_fee": 86,
    "medal_creation": 87,
    "medal_issued": 88,
    "dna_modification_fee": 90,
    "sovereignity_bill": 91,
    "bounty_prize_corporation_tax": 92,
    "agent_mission_reward_corporation_tax": 93,
    "agent_mission_time_bonus_reward_corporation_tax": 94,
    "upkeep_adjustment_fee": 95,
    "planetary_import_tax": 96,
    "planetary_export_tax": 97,
    "planetary_construction": 98,
    "corporate_reward_payout": 99,
    "bounty_surcharge": 101,
    "contract_reversal": 102,
    "corporate_reward_tax": 103,
    "store_purchase": 106,
    "store_purchase_refund": 107,
    "datacore_fee": 112,
    "war_fee_surrender": 113,
    "war_ally_contract": 114,
    "bounty_reimbursement": 115,
    "kill_right_fee": 116,
    "security_processing_fee": 117,
    "industry_job_tax": 120,
    "infrastructure_hub_maintenance": 122,
    "asset_safety_recovery_tax": 123,
    "opportunity_reward": 124,
    "project_discovery_reward": 125,
    "project_discovery_tax": 126,
    "reprocessing_tax": 127,
    "jump_clone_activation_fee": 128,
    "operation_bonus": 129,
    "resource_wars_reward": 131,
    "duel_wager_escrow": 132,
    "duel_wager_payment": 133,
    "duel_wager_refund": 134,
    "reaction": 135,
    "external_trade_freeze": 136,
    "external_trade_thaw": 137,
    "external_trade_delivery": 138,
    "season_challenge_reward": 139,
    "structure_gate_jump": 140,
    "skill_purchase": 141,
    "item_trader_payment": 142,
    "flux_ticket_sale": 143,
    "flux_payout": 144,
    "flux_tax": 145,
    "flux_ticket_repayment": 146,
    "redeemed_isk_token": 147,
    "daily_challenge_reward": 148,
    "market_provider_tax": 149,
    "ess_escrow_transfer": 155,
    "milestone_reward_payment": 156,
    "under_construction": 166,
    "allignment_based_gate_toll": 168,
    "project_payouts": 170,
    "insurgency_corruption_contribution_reward": 172,
    "insurgency_suppression_contribution_reward": 173,
    "daily_goal_payouts": 174,
    "daily_goal_payouts_tax": 175,
    "cosmetic_market_component_item_purchase": 178,
    "cosmetic_market_skin_sale_broker_fee": 179,
    "cosmetic_market_skin_purchase": 180,
    "cosmetic_market_skin_sale": 181,
    "cosmetic_market_skin_sale_tax": 182,
    "cosmetic_market_skin_transaction": 183,
    "skyhook_claim_fee": 184,
    "air_career_program_reward": 185,
    "freelance_jobs_duration_fee": 186,
    "freelance_jobs_broadcasting_fee": 187,
    "freelance_jobs_reward_escrow": 188,
    "freelance_jobs_reward": 189,
    "freelance_jobs_escrow_refund": 190,
    "freelance_jobs_reward_corporation_tax": 191,
    "gm_plex_fee_refund": 192,
}

# 创建id到ref_type的反向映射
id_to_ref_type = {v: k for k, v in ref_type_to_id.items()}

# ESI类型列表
esi_types = [
    "acceleration_gate_fee", "advertisement_listing_fee", "agent_donation", "agent_location_services",
    "agent_miscellaneous", "agent_mission_collateral_paid", "agent_mission_collateral_refunded", "agent_mission_reward",
    "agent_mission_reward_corporation_tax", "agent_mission_time_bonus_reward",
    "agent_mission_time_bonus_reward_corporation_tax", "agent_security_services", "agent_services_rendered",
    "agents_preward", "air_career_program_reward", "alliance_maintainance_fee", "alliance_registration_fee",
    "allignment_based_gate_toll", "asset_safety_recovery_tax", "bounty", "bounty_prize", "bounty_prize_corporation_tax",
    "bounty_prizes", "bounty_reimbursement", "bounty_surcharge", "brokers_fee", "clone_activation", "clone_transfer",
    "contraband_fine", "contract_auction_bid", "contract_auction_bid_corp", "contract_auction_bid_refund",
    "contract_auction_sold", "contract_brokers_fee", "contract_brokers_fee_corp", "contract_collateral",
    "contract_collateral_deposited_corp", "contract_collateral_payout", "contract_collateral_refund",
    "contract_deposit", "contract_deposit_corp", "contract_deposit_refund", "contract_deposit_sales_tax",
    "contract_price", "contract_price_payment_corp", "contract_reversal", "contract_reward",
    "contract_reward_deposited", "contract_reward_deposited_corp", "contract_reward_refund", "contract_sales_tax",
    "copying", "corporate_reward_payout", "corporate_reward_tax", "corporation_account_withdrawal",
    "corporation_bulk_payment", "corporation_dividend_payment", "corporation_liquidation",
    "corporation_logo_change_cost", "corporation_payment", "corporation_registration_fee",
    "cosmetic_market_component_item_purchase", "cosmetic_market_skin_purchase", "cosmetic_market_skin_sale",
    "cosmetic_market_skin_sale_broker_fee", "cosmetic_market_skin_sale_tax", "cosmetic_market_skin_transaction",
    "courier_mission_escrow", "cspa", "cspaofflinerefund", "daily_challenge_reward", "daily_goal_payouts",
    "daily_goal_payouts_tax", "datacore_fee", "dna_modification_fee", "docking_fee", "duel_wager_escrow",
    "duel_wager_payment", "duel_wager_refund", "ess_escrow_transfer", "external_trade_delivery",
    "external_trade_freeze", "external_trade_thaw", "factory_slot_rental_fee", "flux_payout", "flux_tax",
    "flux_ticket_repayment", "flux_ticket_sale", "freelance_jobs_broadcasting_fee", "freelance_jobs_duration_fee",
    "freelance_jobs_escrow_refund", "freelance_jobs_reward", "freelance_jobs_reward_corporation_tax",
    "freelance_jobs_reward_escrow", "gm_cash_transfer", "gm_plex_fee_refund", "industry_job_tax",
    "infrastructure_hub_maintenance", "inheritance", "insurance", "insurgency_corruption_contribution_reward",
    "insurgency_suppression_contribution_reward", "item_trader_payment", "jump_clone_activation_fee",
    "jump_clone_installation_fee", "kill_right_fee", "lp_store", "manufacturing", "market_escrow", "market_fine_paid",
    "market_provider_tax", "market_transaction", "medal_creation", "medal_issued", "milestone_reward_payment",
    "mission_completion", "mission_cost", "mission_expiration", "mission_reward", "office_rental_fee",
    "operation_bonus", "opportunity_reward", "planetary_construction", "planetary_export_tax", "planetary_import_tax",
    "player_donation", "player_trading", "project_discovery_reward", "project_discovery_tax", "project_payouts",
    "reaction", "redeemed_isk_token", "release_of_impounded_property", "repair_bill", "reprocessing_tax",
    "researching_material_productivity", "researching_technology", "researching_time_productivity",
    "resource_wars_reward", "reverse_engineering", "season_challenge_reward", "security_processing_fee", "shares",
    "skill_purchase", "skyhook_claim_fee", "sovereignity_bill", "store_purchase", "store_purchase_refund",
    "structure_gate_jump", "transaction_tax", "under_construction", "upkeep_adjustment_fee", "war_ally_contract",
    "war_fee", "war_fee_surrender"
]

# 在ref_type_to_id字典定义后添加语言顺序
LANGUAGE_ORDER = [
    "en",  # 英语
    "zh",  # 中文
    # "ja",  # 日语
    # "ko",  # 韩语
    # "ru",  # 俄语
    # "de",  # 德语
    # "fr",  # 法语
    # "es",  # 西班牙语
    # "it",  # 意大利语
]


def load_json_file(file_path):
    """加载JSON文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return {}


def save_json_file(data, file_path):
    """保存JSON文件"""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"Successfully saved to {file_path}")
    except Exception as e:
        print(f"Error saving to {file_path}: {e}")


def get_language_code(dir_path):
    """从目录路径中提取语言代码"""
    return os.path.basename(dir_path)


def compare_ref_types_with_accounting_types(ref_type_to_id, accounting_types):
    """比较ref_type与会计类型，找出缺失的类型"""
    # 从accounting_types中提取所有ID
    accounting_ids = set()
    for entry_id in accounting_types.keys():
        try:
            accounting_ids.add(int(entry_id))
        except ValueError:
            pass

    # 找出在ref_type中存在但在accounting_types中不存在的类型
    missing_in_accounting = []
    for ref_type, ref_id in ref_type_to_id.items():
        if ref_id not in accounting_ids:
            missing_in_accounting.append((ref_type, ref_id))

    # 找出在accounting_types中存在但在ref_type中不存在的类型
    missing_in_ref_type = []
    for entry_id in accounting_ids:
        if entry_id not in id_to_ref_type:
            missing_in_ref_type.append(entry_id)

    return missing_in_accounting, missing_in_ref_type


def compare_ref_types_with_esi_types(ref_type_to_id, esi_types):
    """比较ref_type与ESI类型，找出缺失的类型"""
    # 找出在ref_type中存在但在esi_types中不存在的类型
    missing_in_esi = []
    for ref_type in ref_type_to_id.keys():
        if ref_type not in esi_types:
            missing_in_esi.append(ref_type)

    # 找出在esi_types中存在但在ref_type中不存在的类型
    missing_in_ref_type = []
    for esi_type in esi_types:
        if esi_type not in ref_type_to_id:
            missing_in_ref_type.append(esi_type)

    return missing_in_esi, missing_in_ref_type


def create_ordered_dict_by_language(data):
    """创建按指定语言顺序排序的字典"""
    ordered_dict = {}
    for lang in LANGUAGE_ORDER:
        if lang in data:
            ordered_dict[lang] = data[lang]
    return ordered_dict


def main():
    # 加载accountingentrytypes.json
    base_dir = os.path.dirname(os.path.abspath(__file__))
    accounting_types_file = os.path.join(base_dir, "static_data", "accountingentrytypes.json")
    accounting_types = load_json_file(accounting_types_file)

    # 过滤掉key大于10000的项目
    filtered_accounting_types = {k: v for k, v in accounting_types.items() if int(k) <= 10000}
    print(f"过滤前项目数: {len(accounting_types)}, 过滤后项目数: {len(filtered_accounting_types)}")

    # 比较ref_type与会计类型
    missing_in_accounting, missing_in_ref_type = compare_ref_types_with_accounting_types(ref_type_to_id,
                                                                                         filtered_accounting_types)

    print("\n=== wallet_journal_ref 与会计类型比较 ===")
    print(f"wallet_journal_ref 总数: {len(ref_type_to_id)}")
    print(f"会计类型总数: {len(filtered_accounting_types)}")

    print("\n在 wallet_journal_ref 中存在但在 accountingentrytypes 中缺失的类型:")
    for ref_type, ref_id in missing_in_accounting:
        print(f"  - {ref_type} (ID: {ref_id})")

    print("\n在 accountingentrytypes 中存在但在 从wallet_journal_ref 中缺失的类型:")
    for entry_id in missing_in_ref_type:
        print(f"  - ID: {entry_id}")

    # 比较ref_type与ESI类型
    missing_in_esi, missing_in_ref_type_esi = compare_ref_types_with_esi_types(ref_type_to_id, esi_types)

    print("\n=== ref_type与ESI类型比较 ===")
    print(f"wallet_journal_ref总数: {len(ref_type_to_id)}")
    print(f"ESI类型总数: {len(esi_types)}")

    print("\n在 wallet_journal_ref 中存在但在ESI类型中缺失的类型:")
    for ref_type in missing_in_esi:
        print(f"  - {ref_type} (ID: {ref_type_to_id[ref_type]})")

    print("\n在ESI类型中存在但在 wallet_journal_ref 中缺失的类型:")
    for esi_type in missing_in_ref_type_esi:
        print(f"  - {esi_type}")

    # 获取所有语言目录
    extra_dir = os.path.join(base_dir, "extra")
    language_dirs = [d for d in glob.glob(os.path.join(extra_dir, "*")) if os.path.isdir(d)]

    # 加载所有语言的本地化数据
    localization_data = {}
    for lang_dir in language_dirs:
        lang_code = get_language_code(lang_dir)
        json_file = os.path.join(lang_dir, f"{lang_code}_localization.json")
        if os.path.exists(json_file):
            localization_data[lang_code] = load_json_file(json_file)
            print(f"Loaded localization data for {lang_code}")

    # 创建新的数据结构
    new_accounting_types = {}

    # 用于跟踪已使用的ref_type，以便处理重复项
    used_ref_types = {}

    # 处理每个会计条目类型
    for entry_id, entry_data in filtered_accounting_types.items():
        try:
            entry_id_int = int(entry_id)
            # 检查ID是否在id_to_ref_type映射中
            if entry_id_int in id_to_ref_type:
                new_entry = {}

                # 处理entryTypeName
                if "entryTypeNameID" in entry_data:
                    if isinstance(entry_data["entryTypeNameID"], list):
                        entry_type_name = {}
                        # 首先处理所有语言的翻译
                        all_translations = {"en": []}
                        for name_id in entry_data["entryTypeNameID"]:
                            if "entryTypeNameTranslated" in entry_data:
                                all_translations["en"].append(entry_data.get("entryTypeNameTranslated", ""))

                        for lang_code, lang_data in localization_data.items():
                            all_translations[lang_code] = []
                            for name_id in entry_data["entryTypeNameID"]:
                                if str(name_id) in lang_data:
                                    all_translations[lang_code].append(lang_data[str(name_id)]["text"])

                        # 按指定顺序创建最终字典
                        entry_type_name = create_ordered_dict_by_language(all_translations)
                    else:
                        # 处理单个ID的情况
                        all_translations = {"en": [entry_data.get("entryTypeNameTranslated", "")]}
                        for lang_code, lang_data in localization_data.items():
                            if str(entry_data["entryTypeNameID"]) in lang_data:
                                all_translations[lang_code] = [lang_data[str(entry_data["entryTypeNameID"])]["text"]]

                        entry_type_name = create_ordered_dict_by_language(all_translations)

                    new_entry["entryTypeName"] = entry_type_name

                # 处理entryJournalMessage
                if "entryJournalMessageID" in entry_data:
                    if isinstance(entry_data["entryJournalMessageID"], list):
                        all_translations = {"en": []}
                        for message_id in entry_data["entryJournalMessageID"]:
                            if "entryJournalMessageTranslated" in entry_data:
                                all_translations["en"].append(entry_data.get("entryJournalMessageTranslated", ""))

                        for lang_code, lang_data in localization_data.items():
                            all_translations[lang_code] = []
                            for message_id in entry_data["entryJournalMessageID"]:
                                if str(message_id) in lang_data:
                                    all_translations[lang_code].append(lang_data[str(message_id)]["text"])

                        entry_journal_message = create_ordered_dict_by_language(all_translations)
                    else:
                        all_translations = {"en": [entry_data.get("entryJournalMessageTranslated", "")]}
                        for lang_code, lang_data in localization_data.items():
                            if str(entry_data["entryJournalMessageID"]) in lang_data:
                                all_translations[lang_code] = [
                                    lang_data[str(entry_data["entryJournalMessageID"])]["text"]]

                        entry_journal_message = create_ordered_dict_by_language(all_translations)

                    new_entry["entryJournalMessage"] = entry_journal_message

                # 只有当至少有一个字段时才添加到新数据中
                if new_entry:
                    ref_type = id_to_ref_type[entry_id_int]

                    # 检查是否已经使用过这个ref_type
                    if ref_type in used_ref_types:
                        # 如果已经使用过，添加一个数字后缀
                        used_ref_types[ref_type] += 1
                        new_key = f"{ref_type}_{used_ref_types[ref_type]}"
                        print(f"重复的ref_type: {ref_type}，重命名为 {new_key}")
                    else:
                        # 第一次使用这个ref_type
                        used_ref_types[ref_type] = 0
                        new_key = ref_type

                    # 使用ref_type作为键
                    new_accounting_types[new_key] = new_entry
        except ValueError:
            # 如果entry_id不是整数，跳过
            continue

    # 保存新的JSON文件
    output_file = os.path.join(base_dir, "output", "accountingentrytypes_localized.json")
    save_json_file(new_accounting_types, output_file)

    print(f"本地化处理完成！共处理了 {len(new_accounting_types)} 个条目。")


if __name__ == "__main__":
    main()
