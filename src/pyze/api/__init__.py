from .credentials import CredentialStore, FileCredentialStore, BasicCredentialStore
from .gigya import Gigya
from .kamereon import Kamereon, Vehicle, ChargeState, PlugState
from .schedule import ChargeSchedule, ScheduledCharge, ChargeMode

AVAILABLE_LOCALES = [
    "bg_BG",
    "cs_CZ",
    "da_DK",
    "de_DE",
    "de_AT",
    "de_CH",
    "en_GB",
    "en_IE",
    "es_ES",
    "es_MX",
    "fi_FI",
    "fr_FR",
    "fr_BE",
    "fr_CH",
    "fr_LU",
    "hr_HR",
    "hu_HU",
    "it_IT",
    "it_CH",
    "nl_NL",
    "nl_BE",
    "no_NO",
    "pl_PL",
    "pt_PT",
    "ro_RO",
    "ru_RU",
    "sk_SK",
    "sl_SI",
    "sv_SE",
]
