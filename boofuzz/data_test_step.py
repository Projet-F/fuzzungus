import attr

from . import helpers


@attr.s
class DataTestStep:
    type = attr.ib()
    description = attr.ib()
    data = attr.ib()
    timestamp = attr.ib()
    truncated = attr.ib(type=bool)

    @property
    def text_render(self):
        return helpers.format_log_msg(
            msg_type=self.type,
            description=self.description,
            data=self.data,
            timestamp=self.timestamp,
            truncated=self.truncated,
            format_type="terminal",
        )

    @property
    def html_log_line(self):
        return helpers.format_log_msg(
            msg_type=self.type,
            description=self.description,
            data=self.data,
            timestamp=self.timestamp,
            truncated=self.truncated,
            format_type="html",
        )

    @property
    def css_class(self):
        return helpers.test_step_info[self.type]["css_class"]
