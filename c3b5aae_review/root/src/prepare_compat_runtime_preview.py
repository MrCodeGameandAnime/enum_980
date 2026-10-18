"""Prepare a separate pinned experimental runtime and apply review-only patches."""

from pathlib import Path
import difflib
import hashlib
import json
import shutil

PROJECT = Path(__file__).resolve().parents[3]
ROOT = Path(__file__).resolve().parents[1]
SOURCE = PROJECT / "root/results/clean-checkout/root/build/pr1061/core"
TARGET = ROOT / "build/compat-core"
PATCHES = ROOT / "patches"


def replace_once(text, old, new):
    if text.count(old) != 1:
        raise ValueError("Unexpected source anchor: " + old[:100])
    return text.replace(old, new, 1)


if not TARGET.exists():
    shutil.copytree(
        SOURCE, TARGET, ignore=shutil.ignore_patterns(".git", "build-*", "__pycache__")
    )
originals = {
    name: (SOURCE / name).read_text(encoding="utf-8")
    for name in ("py/obj.c", "py/objdict.c", "py/objtype.c")
}
text = originals["py/obj.c"]
text = replace_once(
    text,
    "void mp_obj_print_helper(const mp_print_t *print, mp_obj_t o_in, mp_print_kind_t kind) {",
    """void mp_obj_print_helper(const mp_print_t *print, mp_obj_t o_in, mp_print_kind_t kind) {
    #if MICROPY_PY_JSON
    // JSON encodes string storage, independently of a subclass's Python repr.
    if (kind == PRINT_JSON) {
        mp_obj_t native = mp_obj_cast_to_native_base(o_in, MP_OBJ_FROM_PTR(&mp_type_str));
        if (native != MP_OBJ_NULL && native != o_in) {
            mp_obj_print_helper(print, native, kind);
            return;
        }
    }
    #endif""",
)
(TARGET / "py/obj.c").write_text(text, encoding="utf-8")
text = originals["py/objdict.c"]
text = replace_once(
    text,
    "bool add_quote = MICROPY_PY_JSON && kind == PRINT_JSON && !mp_obj_is_str_or_bytes(next->key);",
    """bool add_quote = MICROPY_PY_JSON && kind == PRINT_JSON && !mp_obj_is_str_or_bytes(next->key);
        #if MICROPY_PY_JSON
        if (add_quote && mp_obj_cast_to_native_base(next->key, MP_OBJ_FROM_PTR(&mp_type_str)) != MP_OBJ_NULL) {
            add_quote = false;
        }
        #endif""",
)
json_dict_text = text
text = replace_once(
    text,
    "            // update from a generic iterable of pairs",
    """            // Mapping protocol takes precedence over iterable-of-pairs input.
            mp_obj_t keys_method[2];
            mp_load_method_maybe(args[1], MP_QSTR_keys, keys_method);
            if (keys_method[0] != MP_OBJ_NULL) {
                mp_obj_t keys = mp_call_method_n_kw(0, 0, keys_method);
                mp_obj_t iter = mp_getiter(keys, NULL);
                mp_obj_t key;
                while ((key = mp_iternext(iter)) != MP_OBJ_STOP_ITERATION) {
                    mp_obj_t value = mp_obj_subscr(args[1], key, MP_OBJ_SENTINEL);
                    mp_map_lookup(&self->map, key, MP_MAP_LOOKUP_ADD_IF_NOT_FOUND)->value = value;
                }
            } else {
            // update from a generic iterable of pairs""",
)
text = replace_once(
    text,
    "    // update the dict with any keyword args",
    "    } // generic iterable branch\n\n    // update the dict with any keyword args",
)
start = text.index("            // update from a generic iterable of pairs")
end = text.index("\n        }\n    }\n\n    } // generic iterable branch", start)
text = (
    text[:start]
    + "".join("    " + line if line.strip() else line for line in text[start:end].splitlines(True))
    + "\n            }\n        }\n    }\n"
    + text[end + len("\n        }\n    }\n\n    } // generic iterable branch") :]
)
(TARGET / "py/objdict.c").write_text(text, encoding="utf-8")
text = originals["py/objtype.c"]
text = replace_once(
    text,
    "static void type_print(const mp_print_t *print, mp_obj_t self_in, mp_print_kind_t kind) {\n    (void)kind;",
    """static void type_print(const mp_print_t *print, mp_obj_t self_in, mp_print_kind_t kind) {
    #if MICROPY_PY_METACLASS_OPS
    const mp_obj_type_t *meta = mp_obj_get_type(self_in);
    if (meta != &mp_type_type) {
        mp_obj_t method[3] = {MP_OBJ_NULL};
        mp_load_method_maybe(MP_OBJ_FROM_PTR(meta), kind == PRINT_STR ? MP_QSTR___str__ : MP_QSTR___repr__, method);
        if (method[0] == MP_OBJ_NULL && kind == PRINT_STR) {
            mp_load_method_maybe(MP_OBJ_FROM_PTR(meta), MP_QSTR___repr__, method);
        }
        if (method[0] != MP_OBJ_NULL) {
            method[2] = self_in;
            mp_obj_t value = mp_call_method_n_kw(1, 0, method);
            if (!mp_obj_is_str(value)) {
                mp_raise_TypeError(MP_ERROR_TEXT("metaclass repr must return str"));
            }
            mp_obj_print_helper(print, value, PRINT_STR);
            return;
        }
    }
    #else
    (void)kind;
    #endif""",
)
text = replace_once(
    text,
    "static void type_attr(mp_obj_t self_in, qstr attr, mp_obj_t *dest) {",
    """static void type_attr_raw(mp_obj_t self_in, qstr attr, mp_obj_t *dest);

static mp_obj_t type_setattr(mp_obj_t cls, mp_obj_t name, mp_obj_t value) {
    mp_obj_t dest[2] = {MP_OBJ_SENTINEL, value};
    type_attr_raw(cls, mp_obj_str_get_qstr(name), dest);
    if (dest[0] != MP_OBJ_NULL) {
        mp_raise_msg(&mp_type_AttributeError, MP_ERROR_TEXT("cannot set class attribute"));
    }
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_3(type_setattr_obj, type_setattr);

static mp_obj_t type_delattr(mp_obj_t cls, mp_obj_t name) {
    mp_obj_t dest[2] = {MP_OBJ_SENTINEL, MP_OBJ_NULL};
    type_attr_raw(cls, mp_obj_str_get_qstr(name), dest);
    if (dest[0] != MP_OBJ_NULL) {
        mp_raise_msg(&mp_type_AttributeError, MP_ERROR_TEXT("class attribute not found"));
    }
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_2(type_delattr_obj, type_delattr);

static void type_attr_raw(mp_obj_t self_in, qstr attr, mp_obj_t *dest) {""",
)
text = replace_once(
    text,
    "        // Only provide type.__new__ when looking up __new__ on the type class itself",
    """        if (self == &mp_type_type && attr == MP_QSTR___setattr__) {
            dest[0] = MP_OBJ_FROM_PTR(&type_setattr_obj);
            return;
        }
        if (self == &mp_type_type && attr == MP_QSTR___delattr__) {
            dest[0] = MP_OBJ_FROM_PTR(&type_delattr_obj);
            return;
        }
        // Only provide type.__new__ when looking up __new__ on the type class itself""",
)
text = replace_once(
    text,
    "#if MICROPY_PY_METACLASS_OPS\nstatic mp_obj_t type_unary_op",
    """static void type_attr(mp_obj_t self_in, qstr attr, mp_obj_t *dest) {
    #if MICROPY_PY_METACLASS_OPS
    const mp_obj_type_t *meta = mp_obj_get_type(self_in);
    if (dest[0] != MP_OBJ_NULL && meta != &mp_type_type) {
        mp_obj_t method[5] = {MP_OBJ_NULL};
        bool deleting = dest[1] == MP_OBJ_NULL;
        mp_load_method_maybe(MP_OBJ_FROM_PTR(meta), deleting ? MP_QSTR___delattr__ : MP_QSTR___setattr__, method);
        if (method[0] != MP_OBJ_NULL) {
            method[2] = self_in;
            method[3] = MP_OBJ_NEW_QSTR(attr);
            method[4] = dest[1];
            mp_call_method_n_kw(deleting ? 2 : 3, 0, method);
            dest[0] = MP_OBJ_NULL;
            return;
        }
    }
    #endif
    type_attr_raw(self_in, attr, dest);
}

#if MICROPY_PY_METACLASS_OPS
static mp_obj_t type_subscr(mp_obj_t self_in, mp_obj_t index, mp_obj_t value) {
    const mp_obj_type_t *meta = mp_obj_get_type(self_in);
    if (meta == &mp_type_type) {
        return MP_OBJ_NULL;
    }
    qstr name = value == MP_OBJ_SENTINEL ? MP_QSTR___getitem__ :
        value == MP_OBJ_NULL ? MP_QSTR___delitem__ : MP_QSTR___setitem__;
    mp_obj_t method[5] = {MP_OBJ_NULL};
    mp_load_method_maybe(MP_OBJ_FROM_PTR(meta), name, method);
    if (method[0] == MP_OBJ_NULL) {
        return MP_OBJ_NULL;
    }
    method[2] = self_in;
    method[3] = index;
    method[4] = value;
    return mp_call_method_n_kw(value == MP_OBJ_SENTINEL || value == MP_OBJ_NULL ? 2 : 3, 0, method);
}

static mp_obj_t type_unary_op""",
)
text = replace_once(
    text,
    "    unary_op, type_unary_op,\n    binary_op, type_binary_op,",
    "    unary_op, type_unary_op,\n    binary_op, type_binary_op,\n    subscr, type_subscr,",
)
text = replace_once(
    text,
    "static mp_obj_t mp_obj_is_subclass(mp_obj_t object, mp_obj_t classinfo);",
    """static mp_obj_t mp_obj_is_subclass(mp_obj_t object, mp_obj_t classinfo);

static bool is_type_object(mp_const_obj_t object) {
    return mp_obj_is_obj(object) &&
        mp_obj_is_subclass_fast(MP_OBJ_FROM_PTR(mp_obj_get_type(object)), MP_OBJ_FROM_PTR(&mp_type_type));
}""",
)
text = text.replace(
    "if (!mp_obj_is_type(object, &mp_type_type)) {", "if (!is_type_object(object)) {"
)
start = text.index("    bool is_class = mp_obj_is_type(classinfo, &mp_type_type);")
end = text.index("    if (is_class) {", start)
text = text[:start] + "    bool is_class = is_type_object(classinfo);\n\n" + text[end:]
text = text.replace(
    "second_arg_type == &mp_type_type ? args[1]", "is_type_object(args[1]) ? args[1]"
)
text = text.replace(
    "assert(mp_obj_is_type(self->type, &mp_type_type));", "assert(is_type_object(self->type));"
)
text = text.replace(
    "assert(mp_obj_is_type(items[i], &mp_type_type));", "assert(is_type_object(items[i]));"
)
text = replace_once(
    text,
    "            // Check if metaclass has custom __new__ (not inherited from type)",
    """            size_t base_count;
            mp_obj_t *base_items;
            if (!mp_obj_is_type(args[1], &mp_type_tuple)) {
                mp_raise_TypeError(MP_ERROR_TEXT("bases must be a tuple"));
            }
            mp_obj_tuple_get(args[1], &base_count, &base_items);
            for (size_t i = 0; i < base_count; ++i) {
                if (!is_type_object(base_items[i])) {
                    mp_raise_TypeError(MP_ERROR_TEXT("bases must be types"));
                }
                const mp_obj_type_t *candidate = mp_obj_get_type(base_items[i]);
                if (mp_obj_is_subclass_fast(MP_OBJ_FROM_PTR(type_in), MP_OBJ_FROM_PTR(candidate))) {
                    continue;
                }
                if (!mp_obj_is_subclass_fast(MP_OBJ_FROM_PTR(candidate), MP_OBJ_FROM_PTR(type_in))) {
                    mp_raise_TypeError(MP_ERROR_TEXT("metaclass conflict"));
                }
                type_in = candidate;
            }
            // Check if metaclass has custom __new__ (not inherited from type)""",
)
start = text.index("            // Found custom __call__, call it with (cls, *args, **kwargs)")
end = text.index("            return result;", start) + len("            return result;")
text = (
    text[:start]
    + """            // Method binding plus cls and every positional/keyword argument.
            size_t count = 3 + n_args + 2 * n_kw;
            mp_obj_t stack_args[8];
            mp_obj_t *new_args = count <= MP_ARRAY_SIZE(stack_args) ? stack_args : m_new(mp_obj_t, count);
            new_args[0] = dest[0];
            new_args[1] = dest[1];
            new_args[2] = self_in;
            memcpy(new_args + 3, args, sizeof(mp_obj_t) * (n_args + 2 * n_kw));
            mp_obj_t result = mp_call_method_n_kw(n_args + 1, n_kw, new_args);
            if (new_args != stack_args) {
                m_del(mp_obj_t, new_args, count);
            }
            return result;"""
    + text[end:]
)
text = text.replace(
    "static mp_obj_t type_setattr(mp_obj_t cls, mp_obj_t name, mp_obj_t value) {",
    'static mp_obj_t type_setattr(mp_obj_t cls, mp_obj_t name, mp_obj_t value) {\n    if (!is_type_object(cls)) { mp_raise_TypeError(MP_ERROR_TEXT("expected type")); }',
)
text = text.replace(
    "static mp_obj_t type_delattr(mp_obj_t cls, mp_obj_t name) {",
    'static mp_obj_t type_delattr(mp_obj_t cls, mp_obj_t name) {\n    if (!is_type_object(cls)) { mp_raise_TypeError(MP_ERROR_TEXT("expected type")); }',
)
(TARGET / "py/objtype.c").write_text(text, encoding="utf-8")
PATCHES.mkdir(exist_ok=True)
for label, names in (
    ("json-string-subclasses", ("py/obj.c", "py/objdict.c")),
    ("metaclass-operations", ("py/objtype.c",)),
):
    diff = "".join(
        "".join(
            difflib.unified_diff(
                originals[name].splitlines(True),
                (
                    json_dict_text
                    if label == "json-string-subclasses" and name == "py/objdict.c"
                    else (TARGET / name).read_text()
                ).splitlines(True),
                fromfile="a/" + name,
                tofile="b/" + name,
            )
        )
        for name in names
    )
    (PATCHES / (label + ".patch")).write_text(diff, encoding="utf-8", newline="\n")
mapping_diff = "".join(
    difflib.unified_diff(
        json_dict_text.splitlines(True),
        (TARGET / "py/objdict.c").read_text().splitlines(True),
        fromfile="a/py/objdict.c",
        tofile="b/py/objdict.c",
    )
)
(PATCHES / "dictionary-mapping-input.patch").write_text(
    mapping_diff, encoding="utf-8", newline="\n"
)
(ROOT / "build/runtime-source.json").write_text(
    json.dumps(
        {
            "repository": "andrewleech/micropython",
            "revision": "6a56288ad12aca9d99d1e425e1400a53c65aa709",
            "experimental": True,
            "source_sha256": {
                name: hashlib.sha256((SOURCE / name).read_bytes()).hexdigest()
                for name in originals
            },
        },
        indent=2,
    )
    + "\n"
)
print(TARGET)
