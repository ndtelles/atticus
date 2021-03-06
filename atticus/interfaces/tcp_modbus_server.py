"""
Copyright (c) 2020 Nathan Telles

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

# from pymodbus.datastore import (ModbusSequentialDataBlock, ModbusServerContext,
#                                 ModbusSlaveContext)
# from pymodbus.device import ModbusDeviceIdentification
# from pymodbus.server.asynchronous import StartTcpServer, StopServer

# from .beak import Beak


# class TCPModbusServer(Beak):
#     # May need to use dynamic inheritance to also support non-sequential
#     class CallbackDataBlock(ModbusSequentialDataBlock):
#         def setValues(self, address: int, values: int) -> None:
#             super().setValues(address, values)

#     def _start(self) -> None:
#         identity = ModbusDeviceIdentification()
#         block = TCPModbusServer.CallbackDataBlock(0x00, [0]*0xff)
#         store = ModbusSlaveContext(
#             di=block,
#             co=block,
#             hr=block,
#             ir=block
#         )
#         context = ModbusServerContext(slaves=store, single=True)

#         # TODO: Does this need to be done in another thread so it doesn't block?
#         StartTcpServer(context, identity=identity, address=("localhost", 5020))

#     def _run(self) -> None:
#         pass

#     def _stop(self) -> None:
#         StopServer()
