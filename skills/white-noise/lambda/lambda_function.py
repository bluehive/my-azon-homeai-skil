# -*- coding: utf-8 -*-
"""ホワイトノイズを最大2時間ループ再生する Alexa スキル (AudioPlayer)。

環境変数:
  AUDIO_URL         HTTPS の音源URL（プレースホルダは要変更）
  MAX_DURATION_SEC  再生上限秒（既定 7200）

開始時刻はトークン "wn:<開始UNIX秒>:<連番>" に埋め込み、状態DBを不要にしている。
"""
import logging
import os
import time

from ask_sdk_core.dispatch_components import (
    AbstractExceptionHandler,
    AbstractRequestHandler,
)
from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.utils import is_intent_name, is_request_type
from ask_sdk_model.interfaces.audioplayer import (
    AudioItem,
    ClearBehavior,
    ClearQueueDirective,
    PlayBehavior,
    PlayDirective,
    StopDirective,
    Stream,
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

AUDIO_URL = os.environ.get("AUDIO_URL", "https://example-bucket.s3.amazonaws.com/white-noise.mp3")
MAX_DURATION_SEC = int(os.environ.get("MAX_DURATION_SEC", "7200"))
TOKEN_PREFIX = "wn"


def make_token(start, seq):
    return "{}:{}:{}".format(TOKEN_PREFIX, int(start), seq)


def parse_token(token):
    try:
        prefix, start, seq = (token or "").split(":")
        if prefix != TOKEN_PREFIX:
            return None, None
        return int(start), int(seq)
    except ValueError:
        return None, None


def play_directive(token, behavior=PlayBehavior.REPLACE_ALL, expected_previous_token=None):
    return PlayDirective(
        play_behavior=behavior,
        audio_item=AudioItem(
            stream=Stream(
                token=token,
                url=AUDIO_URL,
                offset_in_milliseconds=0,
                expected_previous_token=expected_previous_token,
            )
        ),
    )


def start_playback(handler_input):
    token = make_token(time.time(), 0)
    return (
        handler_input.response_builder
        .add_directive(play_directive(token))
        .set_should_end_session(True)
        .response
    )


class LaunchOrPlayHandler(AbstractRequestHandler):
    """起動・再生・再開：追加対話なしで即再生。"""

    def can_handle(self, handler_input):
        return (
            is_request_type("LaunchRequest")(handler_input)
            or is_intent_name("PlayIntent")(handler_input)
            or is_intent_name("AMAZON.ResumeIntent")(handler_input)
            or is_intent_name("AMAZON.StartOverIntent")(handler_input)
        )

    def handle(self, handler_input):
        return start_playback(handler_input)


class StopHandler(AbstractRequestHandler):
    """止めて / キャンセル / 一時停止。"""

    def can_handle(self, handler_input):
        return (
            is_intent_name("AMAZON.StopIntent")(handler_input)
            or is_intent_name("AMAZON.CancelIntent")(handler_input)
            or is_intent_name("AMAZON.PauseIntent")(handler_input)
            or is_intent_name("AMAZON.NavigateHomeIntent")(handler_input)
        )

    def handle(self, handler_input):
        return (
            handler_input.response_builder
            .add_directive(ClearQueueDirective(clear_behavior=ClearBehavior.CLEAR_ALL))
            .add_directive(StopDirective())
            .set_should_end_session(True)
            .response
        )


class HelpHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        speech = "ホワイトノイズを開いて、と言うと2時間再生します。止めて、で停止します。"
        return handler_input.response_builder.speak(speech).ask(speech).response


class UnsupportedIntentHandler(AbstractRequestHandler):
    """ループ/シャッフル/次へ等の未対応標準インテント。"""

    def can_handle(self, handler_input):
        return is_request_type("IntentRequest")(handler_input)

    def handle(self, handler_input):
        return handler_input.response_builder.set_should_end_session(True).response


class NearlyFinishedHandler(AbstractRequestHandler):
    """終わりが近づいたら、上限内なら同じ音源をキューに追加してループ。"""

    def can_handle(self, handler_input):
        return is_request_type("AudioPlayer.PlaybackNearlyFinished")(handler_input)

    def handle(self, handler_input):
        current = handler_input.request_envelope.request.token
        start, seq = parse_token(current)
        rb = handler_input.response_builder
        if start is None:
            return rb.response
        if time.time() - start >= MAX_DURATION_SEC:
            logger.info("max duration reached; not enqueuing")
            return rb.response
        rb.add_directive(
            play_directive(make_token(start, seq + 1), PlayBehavior.ENQUEUE, expected_previous_token=current)
        )
        return rb.response


class PlaybackStartedHandler(AbstractRequestHandler):
    """各トラック開始時に上限超過なら停止（長い音源対策）。"""

    def can_handle(self, handler_input):
        return is_request_type("AudioPlayer.PlaybackStarted")(handler_input)

    def handle(self, handler_input):
        start, _ = parse_token(handler_input.request_envelope.request.token)
        rb = handler_input.response_builder
        if start is not None and time.time() - start >= MAX_DURATION_SEC:
            rb.add_directive(StopDirective())
        return rb.response


class AudioPlayerEventHandler(AbstractRequestHandler):
    """その他の AudioPlayer イベントは応答不要。"""

    def can_handle(self, handler_input):
        return handler_input.request_envelope.request.object_type.startswith("AudioPlayer.")

    def handle(self, handler_input):
        return handler_input.response_builder.response


class PlaybackControllerHandler(AbstractRequestHandler):
    """リモコン/ボタン操作。Play は再生開始、それ以外は停止。"""

    def can_handle(self, handler_input):
        return handler_input.request_envelope.request.object_type.startswith("PlaybackController.")

    def handle(self, handler_input):
        if is_request_type("PlaybackController.PlayCommandIssued")(handler_input):
            return handler_input.response_builder.add_directive(
                play_directive(make_token(time.time(), 0))
            ).response
        return handler_input.response_builder.add_directive(StopDirective()).response


class SessionEndedHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        return handler_input.response_builder.response


class SystemExceptionHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_request_type("System.ExceptionEncountered")(handler_input)

    def handle(self, handler_input):
        logger.error("System.ExceptionEncountered: %s", handler_input.request_envelope.request)
        return handler_input.response_builder.response


class CatchAllExceptionHandler(AbstractExceptionHandler):
    def can_handle(self, handler_input, exception):
        return True

    def handle(self, handler_input, exception):
        logger.error(exception, exc_info=True)
        req_type = handler_input.request_envelope.request.object_type
        rb = handler_input.response_builder
        if req_type.startswith("AudioPlayer.") or req_type.startswith("PlaybackController."):
            return rb.response
        return rb.speak("うまく再生できませんでした。もう一度お試しください。").response


sb = SkillBuilder()
sb.add_request_handler(LaunchOrPlayHandler())
sb.add_request_handler(StopHandler())
sb.add_request_handler(HelpHandler())
sb.add_request_handler(NearlyFinishedHandler())
sb.add_request_handler(PlaybackStartedHandler())
sb.add_request_handler(AudioPlayerEventHandler())
sb.add_request_handler(PlaybackControllerHandler())
sb.add_request_handler(SystemExceptionHandler())
sb.add_request_handler(SessionEndedHandler())
sb.add_request_handler(UnsupportedIntentHandler())  # 最後に置く
sb.add_exception_handler(CatchAllExceptionHandler())

lambda_handler = sb.lambda_handler()
