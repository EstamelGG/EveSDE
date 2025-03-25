# 部分字段缺失，如bounty prizes等，暂时不可用
from dataclasses import dataclass
from typing import Dict, Optional
import json
import requests

accountingentrytypes_map = {
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
    "cosmetic_market_skin_transaction": 183
}

@dataclass
class AccountingEntryType:
    type: str
    name: str
    description: str

class AccountingEntryTypesHandler:
    def __init__(self):
        self.entry_types: Dict[str, AccountingEntryType] = {}
        self._load_data()

    def _load_data(self):
        # 从远程获取数据
        response = requests.get('https://sde.hoboleaks.space/tq/accountingentrytypes.json')
        if response.status_code != 200:
            raise Exception("Failed to fetch accounting entry types data")
        
        data = response.json()
        
        # 处理每个条目
        for type_name, type_id in accountingentrytypes_map.items():
            entry_id = str(type_id)
            if entry_id in data:
                entry_data = data[entry_id]
                # 获取描述字段，按优先级选择
                description = self._get_description(entry_data)
                
                # 创建条目对象
                entry_type = AccountingEntryType(
                    type=type_name,
                    name=entry_data.get('name', ''),
                    description=description
                )
                
                # 存储到映射中
                self.entry_types[type_name] = entry_type

    def _get_description(self, entry_data: dict) -> str:
        """按优先级获取描述字段"""
        # 按优先级检查各个字段
        if entry_data.get('entryJournalMessageTranslated'):
            return entry_data['entryJournalMessageTranslated']
        if entry_data.get('entryTypeDescriptionTranslated'):
            return entry_data['entryTypeDescriptionTranslated']
        if entry_data.get('description'):
            return entry_data['description']
        return entry_data.get('name', '')

    def get_entry_type(self, type_name: str) -> Optional[AccountingEntryType]:
        """获取指定类型的条目"""
        return self.entry_types.get(type_name)

    def get_all_entry_types(self) -> Dict[str, AccountingEntryType]:
        """获取所有条目类型"""
        return self.entry_types

# 使用示例
if __name__ == "__main__":
    handler = AccountingEntryTypesHandler()
    
    # 获取并打印所有条目
    all_entries = handler.get_all_entry_types()
    print(f"Total entries: {len(all_entries)}")
    print("\nAll entries:")
    print("-" * 80)
    for type_name, entry in sorted(all_entries.items()):
        print(f"Type: {entry.type}")
        print(f"Name: {entry.name}")
        print(f"Description: {entry.description}")
        print("-" * 80)
