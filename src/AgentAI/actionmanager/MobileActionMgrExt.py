# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import logging
import math

from .ActionMgr import ActionMgr

MAX_CONTACTS = 10
ACTION_ID_RESET = 0
ACTION_ID_DOWN = 1
ACTION_ID_UP = 2
ACTION_ID_MOVE = 3
ACTION_ID_CLICK = 4  # pyIOService.msghandler.MsgHandler.py(_CreateUIActionList)定义的ACTION_ID_CLICK为4
ACTION_ID_SWIPE = 5  # pyIOService.msghandler.MsgHandler.py(_CreateUIActionList)定义的ACTION_ID_SWIPE为5
ACTION_ID_SWIPEDOWN = 6
ACTION_ID_SWIPEMOVE = 7
ACTION_ID_INPUT_TEXT = 8
ACTION_ID_INPUT_KEY = 9

LOG = logging.getLogger('agent')

class MobileActionMgrExt(object):
    """
    ActionMgr Extension implement for common use, based on ActionMgr
    """
    def __init__(self):
        self.__actionMgr = ActionMgr()
        self.__contactPoints = [None] * MAX_CONTACTS

        self.__movingRadius = None
        self.__movingContact = None
        self.__movingCx = None
        self.__movingCy = None
        self.__movingFlag = False

    def Initialize(self):
        """
        Initialize this module, call ActionMgr.Initialize
        :return:
        """
        return self.__actionMgr.Initialize()

    def Finish(self):
        """
        Finish this module, call ActionMgr.Finish
        :return:
        """
        self.__actionMgr.Finish()

    def Reset(self, frameSeq=-1):
        """
        Call Reset action to reset all contacts to up and clear all the actions in the queue.
        :param frameSeq: the frame sequence, default is -1
        :return:
        """
        actionData = dict()
        actionData['img_id'] = frameSeq
        LOG.debug('send frame data, frameIndex= %d Reset', frameSeq)
        ret = self.__actionMgr.SendAction(actionID=ACTION_ID_RESET, actionData=actionData,
                                          frameSeq=frameSeq)
        if ret:
            self.__contactPoints = [None] * MAX_CONTACTS
            return True
        return False

    def SendAction(self, actionID, actionData, frameSeq=-1):
        """
        Send action to remote(client)
        :param actionID: the self-defined action ID
        :param actionData: the context data of the action ID
        :param frameSeq: the frame sequence, default is -1
        :return:
        """
        return self.__actionMgr.SendAction(actionID=actionID, actionData=actionData,
                                           frameSeq=frameSeq)

    def MovingInit(self, centerX, centerY, radius, contact=0, frameSeq=-1, waitTime=1000):
        """
        Initialize the center point, radius and contact of the moving control panel. Just Down the
        center point and wait some time.
        :param centerX: x of center point
        :param centerY: y of center point
        :param radius: radius of the moving control panel
        :param contact: contact index(0, 1, ..., 9)
        :param frameSeq: the frame sequence, default is -1
        :param waitTime: wait how long(ms) until next action
        :return:
        """
        LOG.debug('MovingInit c({%s}, {%s}) r={%s} contact={%d} Wait {%d}ms',
                  str(centerX), str(centerY), str(radius),contact, waitTime)

        ret = self.Down(centerX, centerY, contact=contact, frameSeq=frameSeq, waitTime=waitTime)
        if ret:
            self.__movingRadius = radius
            self.__movingContact = contact
            self.__movingCx = centerX
            self.__movingCy = centerY
            self.__movingFlag = True
            return True
        return False

    def MovingFinish(self, frameSeq=-1):
        """
        Finsih the the moving control panel. Just Up the contact.
        :param frameSeq: the frame sequence, default is -1
        :return:
        """
        LOG.debug('MovingFinish')
        if self.__movingFlag:
            ret = self.Up(contact=self.__movingContact, frameSeq=frameSeq)
            if ret:
                self.__movingFlag = False
                return True
        return False

    def Moving(self, dirAngle, frameSeq=-1, durationMS=50):
        """
        Move the contact in MovingInit() to the dirAngle point which is computed by center
        point, radius and dirAngle(0:forward, 90:right, 180:backward, 270:left).
        :param dirAngle: the angle([0, 360)) of moving direction
        :param frameSeq: the frame sequence, default is -1
        :param durationMS: the duration time(ms) in this process
        :return:
        """
        LOG.debug('Moving %s', str(dirAngle))
        if not self.__movingFlag:
            return False

        if 0 <= dirAngle < 360:
            dx = self.__movingRadius * math.sin(math.radians(dirAngle))
            dy = self.__movingRadius * math.cos(math.radians(dirAngle))
        else:
            dx = 0
            dy = 0

        px = int(self.__movingCx + dx)
        py = int(self.__movingCy - dy)
        ret = self.SwipeMove(px, py, contact=self.__movingContact, frameSeq=frameSeq,
                             durationMS=durationMS)
        if ret:
            return True
        return False

    def Move(self, px, py, contact=0, frameSeq=-1, waitTime=0):
        """
        Move the contact to the target point(px, py) immediately. No make up points in the process.
        :param px: x of target point
        :param py: y of target point
        :param contact: contact index(0, 1, ..., 9)
        :param frameSeq: the frame sequence, default is -1
        :param waitTime: wait how long(ms) until next action
        :return:
        """
        actionData = self._SinglePointOp(px=px, py=py, contact=contact, wait_time=waitTime)
        actionData['img_id'] = frameSeq

        LOG.debug('send frame data, frameIndex=%d Move ({%d}, {%d}) contact={%d} Wait {%d}ms',
                  frameSeq, px, py, contact, waitTime)

        ret = self.__actionMgr.SendAction(actionID=ACTION_ID_MOVE, actionData=actionData,
                                          frameSeq=frameSeq)
        if ret:
            self.__contactPoints[contact] = (px, py)
            return True
        return False

    def SimulatorKeyAction(self, px, py, contact=0, frameSeq=-1, alphabet="", action_type="", action_text=""):
        """

        :param px:
        :param py:
        :param contact:
        :param frameSeq:
        :param alphabet:
        :param action_type:
        :param action_text:
        :return:
        """
        LOG.debug("simulator key, px:%d, py:%d, contact:%d, frameSeq:%d, alphabet:%s, action_type:%s, action_text:%s",
                  px, py, contact, frameSeq, alphabet, str(action_type), action_text)
        return True

    def Click(self, px, py, contact=0, frameSeq=-1, durationMS=-1):
        """
        Click the target point(px, py) on contact. Just Down the point and wait for durationMS
        and then Up.
        :param px: x of target point
        :param py: y of target point
        :param contact: contact index(0, 1, ..., 9)
        :param frameSeq: the frame sequence, default is -1
        :param durationMS: the duration time(ms) in this process
        :return:
        """
        actionData = self._SinglePointOp(px=px, py=py, contact=contact, during_time=durationMS)
        actionData['img_id'] = frameSeq

        if durationMS < 0:
            LOG.debug('send frame data, frameIndex={%d} Click ({%d}, {%d}) contact={%d}',
                      frameSeq, px, py, contact)
        else:
            LOG.debug('send frame data, frameIndex={%d} Click ({%d}, {%d}) {%d}ms contact={%d}',
                      frameSeq, px, py, durationMS, contact)

        ret = self.__actionMgr.SendAction(actionID=ACTION_ID_CLICK, actionData=actionData,
                                          frameSeq=frameSeq)
        if ret:
            self.__contactPoints[contact] = None
            return True
        return False

    def Down(self, px, py, contact=0, frameSeq=-1, waitTime=0):
        """
        Down the target point(px, py) on contact.
        :param px: x of target point
        :param py: y of target point
        :param contact: contact index(0, 1, ..., 9)
        :param frameSeq: the frame sequence, default is -1
        :param waitTime: wait how long(ms) until next action
        :return:
        """
        actionData = self._SinglePointOp(px=px, py=py, contact=contact, wait_time=waitTime)
        actionData['img_id'] = frameSeq

        LOG.debug('send frame data, frameIndex={%d} Down ({%d}, {%d}) contact={%d} Wait {%d}ms',
                  frameSeq, px, py, contact, waitTime)

        ret = self.__actionMgr.SendAction(actionID=ACTION_ID_DOWN, actionData=actionData,
                                          frameSeq=frameSeq)
        if ret:
            self.__contactPoints[contact] = (px, py)
            return True
        return False

    def Up(self, contact=0, frameSeq=-1, waitTime=0):
        """
        Up the contact.
        :param contact: contact index(0, 1, ..., 9)
        :param frameSeq: the frame sequence, default is -1
        :param waitTime: wait how long(ms) until next action
        :return:
        """
        actionData = self._SinglePointOp(px=0, py=0, contact=contact, wait_time=waitTime)
        actionData['img_id'] = frameSeq

        LOG.debug('send frame data, frameIndex={%d} Up contact={%d} Wait {%d}ms',
                  frameSeq, contact, waitTime)

        ret = self.__actionMgr.SendAction(actionID=ACTION_ID_UP, actionData=actionData,
                                          frameSeq=frameSeq)
        if ret:
            self.__contactPoints[contact] = None
            return True
        return False

    def Swipe(self, sx, sy, ex, ey, contact=0, frameSeq=-1, durationMS=50, needUp=True):
        """
        Swipe from start point(sx, sy) to end point(ex, ey) on contact. The process
        costs durationMS time.
        :param sx: x of start point
        :param sy: y of start point
        :param ex: x of end point
        :param ey: y of end point
        :param contact: contact index(0, 1, ..., 9)
        :param frameSeq: frameSeq
        :param durationMS: the duration time(ms) in this process
        :param needUp: if True, the end point will Up; otherwise, will always Down the end point
        until next action on the contact.
        :return:
        """
        if needUp:
            actionData = self._DoublePointOp(start_x=sx, start_y=sy, end_x=ex, end_y=ey,
                                             contact=contact,
                                             during_time=durationMS)
            actionData['img_id'] = frameSeq

            LOG.debug('send frame data, frameIndex={%d} Swipe({%d}, {%d})->({%d}, {%d}) contact={%d}',
                      frameSeq, sx, sy, ex, ey, contact)

            ret = self.__actionMgr.SendAction(actionID=ACTION_ID_SWIPE, actionData=actionData,
                                              frameSeq=frameSeq)
            if ret:
                self.__contactPoints[contact] = None
                return True
            return False

        actionData = self._DoublePointOp(start_x=sx, start_y=sy, end_x=ex, end_y=ey,
                                         contact=contact,
                                         during_time=durationMS)
        actionData['img_id'] = frameSeq

        LOG.debug('send frame data, frameIndex={%d} SwipeDown({%d}, {%d})->({%d}, {%d}) contact={%d}',
                  frameSeq, sx, sy, ex, ey, contact)

        ret = self.__actionMgr.SendAction(actionID=ACTION_ID_SWIPEDOWN, actionData=actionData,
                                          frameSeq=frameSeq)

        if ret:
            self.__contactPoints[contact] = (ex, ey)
            return True
        return False

    def SwipeMove(self, px, py, contact=0, frameSeq=-1, durationMS=50):
        """
        Move the contact to the target point(px, py) with make up points in the process.
        The process costs durationMS time.
        :param px: x of target point
        :param py: y of target point
        :param contact: contact index(0, 1, ..., 9)
        :param frameSeq: frameSeq
        :param durationMS: the duration time(ms) in this process
        :return:
        """
        if self.__contactPoints[contact] is not None:
            actionData = self._SinglePointOp(px=px, py=py,
                                             contact=contact,
                                             during_time=durationMS)
            actionData['img_id'] = frameSeq

            LOG.debug('send frame data, frameIndex={%d} SwipeMove({%d}, {%d})) contact={%d}',
                      frameSeq, px, py, contact)

            ret = self.__actionMgr.SendAction(actionID=ACTION_ID_SWIPEMOVE, actionData=actionData,
                                              frameSeq=frameSeq)
            if ret:
                self.__contactPoints[contact] = (px, py)
                return True
            return False

        LOG.warning('SwipeMove needs previous Points on contact(%d)', contact)
        return False

    def InputText(self, text, frameSeq=-1, waitTime=0):
        actionData = dict()
        actionData['img_id'] = frameSeq
        actionData['text'] = text
        if waitTime > 0:
            actionData['wait_time'] = waitTime
        return self.__actionMgr.SendAction(actionID=ACTION_ID_INPUT_TEXT, actionData=actionData,
                                           frameSeq=frameSeq)

    def InputKey(self, key, frameSeq=-1, waitTime=0):
        actionData = dict()
        actionData['img_id'] = frameSeq
        actionData['key'] = key
        if waitTime > 0:
            actionData['wait_time'] = waitTime
        return self.__actionMgr.SendAction(actionID=ACTION_ID_INPUT_KEY, actionData=actionData,
                                           frameSeq=frameSeq)

    @staticmethod
    def _SinglePointOp(px, py, contact, during_time=0, wait_time=0):
        msg_data = dict()
        msg_data['px'] = int(px)
        msg_data['py'] = int(py)
        msg_data['contact'] = contact
        if during_time > 0:
            msg_data['during_time'] = during_time
        if wait_time > 0:
            msg_data['wait_time'] = wait_time
        return msg_data

    @staticmethod
    def _key_action_op(px, py, contact, alphabet="", action_type="", action_text= ""):
        msg_data = dict()
        msg_data['px'] = int(px)
        msg_data['py'] = int(py)
        msg_data['contact'] = contact
        msg_data['alphabet'] = alphabet
        msg_data['action_type'] = action_type
        msg_data['action_text'] = action_text
        return msg_data

    @staticmethod
    def _DoublePointOp(start_x, start_y, end_x, end_y, contact,
                       during_time=0, wait_time=0):
        msg_data = dict()
        msg_data['start_x'] = int(start_x)
        msg_data['start_y'] = int(start_y)
        msg_data['end_x'] = int(end_x)
        msg_data['end_y'] = int(end_y)
        msg_data['contact'] = contact
        if during_time > 0:
            msg_data['during_time'] = during_time
        if wait_time > 0:
            msg_data['wait_time'] = wait_time
        return msg_data
