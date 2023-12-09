from abc import ABC

from construct import Container, Struct, Subconstruct, StopFieldError


class TellPlusSizeOf(Subconstruct, ABC):
    def __init__(self, subcon):
        super(TellPlusSizeOf, self).__init__(subcon)
        self.flagbuildnone = True

    def _parse(self, stream, context, path):
        return stream.tell() + self.subcon.sizeof(context=context)

    def _build(self, obj, stream, context, path):
        return b""

    def sizeof(self, context=None, **kw):
        return 0


class TellMinusSizeOf(Subconstruct, ABC):
    def __init__(self, subcon):
        super().__init__(subcon)
        self.flagbuildnone = True

    def _parse(self, stream, context, path):
        return stream.tell() - self.subcon.sizeof(context=context)

    def _build(self, obj, stream, context, path):
        return b""

    def sizeof(self, context=None, **kw):
        return 0


class Embedded(Subconstruct):
    r"""
    Embeds a struct into the enclosing struct, merging fields. Can also embed sequences into sequences. Name is also inherited.

    :param subcon: the struct to embed

    Example::

        >>> EmbeddableStruct("a"/Byte, Embedded(Struct("b"/Byte)), "c"/Byte).parse(b"abc")
        Container(a=97)(b=98)(c=99)
        >>> EmbeddableStruct("a"/Byte, Embedded(Struct("b"/Byte)), "c"/Byte).build(_)
        b'abc'
    """
    def __init__(self, subcon):
        super().__init__(subcon)


class EmbeddableStruct(Struct):
    r"""
    A special Struct that allows embedding of fields with type Embed.
    """

    def __init__(self, *subcons, **subconskw):
        super().__init__(*subcons, **subconskw)

    def _parse(self, stream, context, path):
        r"""
        This is really copy of :func:`~construct.core.Struct._parse` with
        check to merage objects if the subconstruct is :cls:`Embedded`
        """
        obj = Container()
        obj._io = stream
        context = Container(_ = context, _params = context._params, _root = None, _parsing = context._parsing, _building = context._building, _sizing = context._sizing, _subcons = self._subcons, _io = stream, _index = context.get("_index", None), _parent = obj)
        context._root = context._.get("_root", context)
        for sc in self.subcons:
            try:
                subobj = sc._parsereport(stream, context, path)
                if sc.name:
                    obj[sc.name] = subobj
                    context[sc.name] = subobj
                if subobj and not sc.name and isinstance(sc, Embedded) and isinstance(subobj, (dict, list)):
                    obj.update(subobj)
            except StopFieldError:
                break
        return obj

    def _build(self, obj, stream, context, path):
        r"""
        This is really copy of :func:`~construct.core.Struct._build` with
        check to use 'obj' if the subconstruct is :cls:`Embedded`
        """
        if obj is None:
            obj = Container()
        context = Container(_ = context, _params = context._params, _root = None, _parsing = context._parsing, _building = context._building, _sizing = context._sizing, _subcons = self._subcons, _io = stream, _index = context.get("_index", None))
        context._root = context._.get("_root", context)
        context.update(obj)
        for sc in self.subcons:
            try:
                if sc.flagbuildnone:
                    subobj = obj.get(sc.name, None)
                elif not sc.name and isinstance(sc, Embedded):
                    subobj = obj
                else:
                    subobj = obj[sc.name] # raises KeyError

                if sc.name:
                    context[sc.name] = subobj

                buildret = sc._build(subobj, stream, context, path)
                if sc.name:
                    context[sc.name] = buildret
            except StopFieldError:
                break
        return context

