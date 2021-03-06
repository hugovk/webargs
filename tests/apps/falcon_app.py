import falcon
import marshmallow as ma
from webargs import fields
from webargs.core import MARSHMALLOW_VERSION_INFO, json
from webargs.falconparser import parser, use_args, use_kwargs

hello_args = {"name": fields.Str(missing="World", validate=lambda n: len(n) >= 3)}
hello_multiple = {"name": fields.List(fields.Str())}


class HelloSchema(ma.Schema):
    name = fields.Str(missing="World", validate=lambda n: len(n) >= 3)


strict_kwargs = {"strict": True} if MARSHMALLOW_VERSION_INFO[0] < 3 else {}
hello_many_schema = HelloSchema(many=True, **strict_kwargs)

# variant which ignores unknown fields
exclude_kwargs = (
    {"strict": True} if MARSHMALLOW_VERSION_INFO[0] < 3 else {"unknown": ma.EXCLUDE}
)
hello_exclude_schema = HelloSchema(**exclude_kwargs)


class Echo(object):
    def on_get(self, req, resp):
        parsed = parser.parse(hello_args, req, location="query")
        resp.body = json.dumps(parsed)


class EchoForm(object):
    def on_post(self, req, resp):
        parsed = parser.parse(hello_args, req, location="form")
        resp.body = json.dumps(parsed)


class EchoJSON(object):
    def on_post(self, req, resp):
        parsed = parser.parse(hello_args, req)
        resp.body = json.dumps(parsed)


class EchoJSONOrForm(object):
    def on_post(self, req, resp):
        parsed = parser.parse(hello_args, req, location="json_or_form")
        resp.body = json.dumps(parsed)


class EchoUseArgs(object):
    @use_args(hello_args, location="query")
    def on_get(self, req, resp, args):
        resp.body = json.dumps(args)


class EchoUseKwargs(object):
    @use_kwargs(hello_args, location="query")
    def on_get(self, req, resp, name):
        resp.body = json.dumps({"name": name})


class EchoUseArgsValidated(object):
    @use_args(
        {"value": fields.Int()},
        validate=lambda args: args["value"] > 42,
        location="form",
    )
    def on_post(self, req, resp, args):
        resp.body = json.dumps(args)


class EchoJSONIgnoreExtraData(object):
    def on_post(self, req, resp):
        resp.body = json.dumps(parser.parse(hello_exclude_schema, req))


class EchoMulti(object):
    def on_get(self, req, resp):
        resp.body = json.dumps(parser.parse(hello_multiple, req, location="query"))


class EchoMultiForm(object):
    def on_post(self, req, resp):
        resp.body = json.dumps(parser.parse(hello_multiple, req, location="form"))


class EchoMultiJSON(object):
    def on_post(self, req, resp):
        resp.body = json.dumps(parser.parse(hello_multiple, req))


class EchoManySchema(object):
    def on_post(self, req, resp):
        resp.body = json.dumps(parser.parse(hello_many_schema, req))


class EchoUseArgsWithPathParam(object):
    @use_args({"value": fields.Int()}, location="query")
    def on_get(self, req, resp, args, name):
        resp.body = json.dumps(args)


class EchoUseKwargsWithPathParam(object):
    @use_kwargs({"value": fields.Int()}, location="query")
    def on_get(self, req, resp, value, name):
        resp.body = json.dumps({"value": value})


class AlwaysError(object):
    def on_get(self, req, resp):
        def always_fail(value):
            raise ma.ValidationError("something went wrong")

        args = {"text": fields.Str(validate=always_fail)}
        resp.body = json.dumps(parser.parse(args, req))

    on_post = on_get


class EchoHeaders(object):
    def on_get(self, req, resp):
        class HeaderSchema(ma.Schema):
            NAME = fields.Str(missing="World")

        resp.body = json.dumps(
            parser.parse(HeaderSchema(**exclude_kwargs), req, location="headers")
        )


class EchoCookie(object):
    def on_get(self, req, resp):
        resp.body = json.dumps(parser.parse(hello_args, req, location="cookies"))


class EchoNested(object):
    def on_post(self, req, resp):
        args = {"name": fields.Nested({"first": fields.Str(), "last": fields.Str()})}
        resp.body = json.dumps(parser.parse(args, req))


class EchoNestedMany(object):
    def on_post(self, req, resp):
        args = {
            "users": fields.Nested(
                {"id": fields.Int(), "name": fields.Str()}, many=True
            )
        }
        resp.body = json.dumps(parser.parse(args, req))


def use_args_hook(args, context_key="args", **kwargs):
    def hook(req, resp, params):
        parsed_args = parser.parse(args, req=req, **kwargs)
        req.context[context_key] = parsed_args

    return hook


@falcon.before(use_args_hook(hello_args, location="query"))
class EchoUseArgsHook(object):
    def on_get(self, req, resp):
        resp.body = json.dumps(req.context["args"])


def create_app():
    app = falcon.API()
    app.add_route("/echo", Echo())
    app.add_route("/echo_form", EchoForm())
    app.add_route("/echo_json", EchoJSON())
    app.add_route("/echo_json_or_form", EchoJSONOrForm())
    app.add_route("/echo_use_args", EchoUseArgs())
    app.add_route("/echo_use_kwargs", EchoUseKwargs())
    app.add_route("/echo_use_args_validated", EchoUseArgsValidated())
    app.add_route("/echo_ignoring_extra_data", EchoJSONIgnoreExtraData())
    app.add_route("/echo_multi", EchoMulti())
    app.add_route("/echo_multi_form", EchoMultiForm())
    app.add_route("/echo_multi_json", EchoMultiJSON())
    app.add_route("/echo_many_schema", EchoManySchema())
    app.add_route("/echo_use_args_with_path_param/{name}", EchoUseArgsWithPathParam())
    app.add_route(
        "/echo_use_kwargs_with_path_param/{name}", EchoUseKwargsWithPathParam()
    )
    app.add_route("/error", AlwaysError())
    app.add_route("/echo_headers", EchoHeaders())
    app.add_route("/echo_cookie", EchoCookie())
    app.add_route("/echo_nested", EchoNested())
    app.add_route("/echo_nested_many", EchoNestedMany())
    app.add_route("/echo_use_args_hook", EchoUseArgsHook())
    return app
