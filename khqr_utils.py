import config

try:
    import crcmod
except ImportError:
    crcmod = None

class KHQR:
    def __init__(self, currency='USD'):
        self.payload = {}
        # Basic Defaults
        self.payload['00'] = '01' # Payload Format Indicator
        self.payload['01'] = '12' # Dynamic (12) or Static (11)
        self.payload['52'] = '5999' # Merchant Category Code (General)
        
        # Currency: 840=USD, 116=KHR
        if currency == 'KHR':
            self.payload['53'] = '116'
        else:
            self.payload['53'] = '840'
            
        self.payload['58'] = 'KH' # Country Code
        self.payload['60'] = 'Phnom Penh' # Merchant City

    def set_merchant(self, global_id, merchant_id):
        # Tag 29: Merchant Account Information
        # 00: Global Unique Identifier
        # 01: Merchant ID
        nested_data = f"00{len(global_id):02}{global_id}01{len(merchant_id):02}{merchant_id}"
        self.payload['29'] = nested_data

    def set_amount(self, amount):
        val = f"{float(amount):.2f}"
        self.payload['54'] = val

    def set_merchant_name(self, name):
        self.payload['59'] = name

    def set_currency(self, currency_code):
        self.payload['53'] = currency_code

    def _generate_crc16(self, data_str):
        if crcmod:
            try:
                # CRC-16-CCITT (0xFFFF)
                crc16 = crcmod.mkCrcFun(0x11021, initCrc=0xFFFF, rev=False, xorOut=0x0000)
                return hex(crc16(data_str.encode('utf-8')))[2:].upper().zfill(4)
            except Exception:
                pass
        
        # Pure Python Fallback (CCITT-False)
        crc = 0xFFFF
        for char in data_str:
            byte = ord(char)
            crc ^= (byte << 8)
            for _ in range(8):
                if (crc & 0x8000):
                    crc = (crc << 1) ^ 0x1021
                else:
                    crc = crc << 1
            crc &= 0xFFFF
        return hex(crc)[2:].upper().zfill(4)

    def generate_string(self):
        # Sort keys
        sorted_keys = sorted(self.payload.keys())
        raw_string = ""
        
        for key in sorted_keys:
            val = self.payload[key]
            raw_string += f"{key}{len(val):02}{val}"

        # Append CRC Tag ID and Length
        data_to_sign = raw_string + "6304"
        crc_val = self._generate_crc16(data_to_sign)
        
        return data_to_sign + crc_val

# Helper function
def generate_local_khqr(amount=1.00, currency='USD'):
    # Default to generic Bakong merchant for interoperability
    qr = KHQR(currency=currency)
    # Use Configured Merchant Info
    qr.set_merchant(config.KHQR_GLOBAL_ID, config.KHQR_MERCHANT_ID) 
    qr.set_merchant_name(config.KHQR_MERCHANT_NAME)
    qr.set_amount(amount)
    return qr.generate_string()
