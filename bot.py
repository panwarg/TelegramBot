import os

import telebot

from dotenv import load_dotenv

from abc import ABC, abstractmethod
import asyncio
import aiohttp
from tvm_valuetypes import serialize_tvm_stack

from tonsdk.provider import ToncenterClient, SyncTonlibClient, prepare_address, address_state
from tonsdk.utils import TonCurrencyEnum, from_nano
from tonsdk.boc import Cell

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
WALLET_ADDRESS = os.getenv('WALLET_ADDRESS')

bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start', 'hello'])
def send_welcome(message):
    comment = "2e7b37be-5ee4-4285-aee5-94bd0a2e8f9d"
    response = "You need to send 0.01 TON for verification your wallet.\r\n\r\n"
    response += "Send to: " + WALLET_ADDRESS + "\r\n\r\n"
    response += "Comment: " + comment + "\r\n\r\n"
    response += "Important! Don't forget to include comment in transaction!"

    bot.reply_to(message, response)


@bot.message_handler(func=lambda msg: True)
def echo_all(message):
    bot.reply_to(message, message.text)


class AbstractTonClient(ABC):
    @abstractmethod
    def _run(self, to_run, *, single_query=True):
        raise NotImplemented

    def get_address_information(self, address: str,
                                currency_to_show: TonCurrencyEnum = TonCurrencyEnum.ton):
        return self.get_addresses_information([address], currency_to_show)[0]

    def get_addresses_information(self, addresses,
                                  currency_to_show: TonCurrencyEnum = TonCurrencyEnum.ton):
        if not addresses:
            return []

        tasks = []
        for address in addresses:
            address = prepare_address(address)
            tasks.append(self.provider.raw_get_account_state(address))

        results = self._run(tasks, single_query=False)

        for result in results:
            result["state"] = address_state(result)
            if "balance" in result:
                if int(result["balance"]) < 0:
                    result["balance"] = 0
                else:
                    result["balance"] = from_nano(
                        int(result["balance"]), currency_to_show)

        return results
    
    def seqno(self, addr: str):
        addr = prepare_address(addr)
        result = self._run(self.provider.raw_run_method(addr, "seqno", []))

        if 'stack' in result and ('@type' in result and result['@type'] == 'smc.runResult'):
            result['stack'] = serialize_tvm_stack(result['stack'])

        return result

    def send_boc(self, boc: Cell):
        return self._run(self.provider.raw_send_message(boc))


class TonCenterTonClient(AbstractTonClient):
    def __init__(self):
        self.loop = asyncio.get_event_loop()
        self.provider = ToncenterClient(base_url="https://testnet.toncenter.com/api/v2/",
                                        api_key="283fbeecda034eae6e1a1873d499b4576737d1da97eeb650ce7e23f5e2187559")

    def _run(self, to_run, *, single_query=True):
        try:
            return self.loop.run_until_complete(
                self.__execute(to_run, single_query))

        except Exception:  # ToncenterWrongResult, asyncio.exceptions.TimeoutError, aiohttp.client_exceptions.ClientConnectorError
            raise

    async def __execute(self, to_run, single_query):
        timeout = aiohttp.ClientTimeout(total=5)

        async with aiohttp.ClientSession(timeout=timeout) as session:
            if single_query:
                to_run = [to_run]

            tasks = []
            for task in to_run:
                tasks.append(task["func"](
                    session, *task["args"], **task["kwargs"]))

            return await asyncio.gather(*tasks)


class TonLibJsonTonClient(AbstractTonClient):
    def __init__(self):
        self.loop = asyncio.get_event_loop()
        self.provider = SyncTonlibClient(config="./.tonlibjson/testnet.json",
                                         keystore="./.tonlibjson/keystore",
                                         cdll_path="./.tonlibjson/linux_libtonlibjson.so")  # or macos_libtonlibjson.dylib
        self.provider.init()

    def _run(self, to_read, *, single_query=True):
        try:
            if not single_query:
                queries_order = {query_id: i for i,
                                 query_id in enumerate(to_read)}
                return self.provider.read_results(queries_order)

            else:
                return self.provider.read_result(to_read)

        except Exception:  # TonLibWrongResult, TimeoutError
            raise


# create a client instance
client = TonCenterTonClient()

# use client to get any addr information
addr_info = client.get_address_information(
    "EQAhE3sLxHZpsyZ_HecMuwzvXHKLjYx4kEUehhOy2JmCcHCT")

# get your wallet seqno
seqno = client.seqno(wallet.address.to_string())

# send any boc
client.send_boc(nft_boc)

bot.infinity_polling()