"""Loader for Pixfizz exports: tolerates Ruby/ActiveSupport YAML tags."""
import yaml


class PxLoader(yaml.SafeLoader):
    pass


def _any(loader, suffix, node):
    if isinstance(node, yaml.MappingNode):
        return loader.construct_mapping(node, deep=True)
    if isinstance(node, yaml.SequenceNode):
        return loader.construct_sequence(node, deep=True)
    return loader.construct_scalar(node)


PxLoader.add_multi_constructor("", _any)
PxLoader.add_multi_constructor("tag:yaml.org,2002:", _any)


def load(path):
    with open(path) as fh:
        return yaml.load(fh, Loader=PxLoader)
