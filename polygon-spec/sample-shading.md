# Traditional sample shading

This applies to pass-fail, single-pass samples. Interactive and multi-pass
samples retain their existing presentation.

## Producing marks

Use the bundled `testlib.h` in `third_party/testlib/testlib.h`. In a validator,
call `setTestCase(i)` before reading case `i` from `inf`. In a checker, call it
before reading that case's contestant output from `ouf`; reads from `ans` do
not define the output boundaries. Use positive, increasing case numbers.

The runner requests optional markup through `POLYGON_SAMPLE_MARKUP_FILE`.
Authors do not need to set that environment variable themselves. Checker marks
are exported after successful checking. Validators retain the explicit
`--testMarkupFileName` option, which takes precedence over the optional path.

The renderer requires exact agreement between the marked bytes and the sample
being displayed. Boundaries must identify whole lines; unread trailing whitespace
on a line belongs to the preceding case. Odd case numbers are shaded. A leading
case count before the first mark stays plain. Missing, invalid, oversized, or
mismatched marks fall back to plain samples, without changing judging results.
Do not infer output groups from line counts or from `ans` read positions.

## Display controls

Shading is enabled by default. Contest property `shadeSamples` accepts only
`true` or `false`, without a language suffix. In Contest Properties, **Remove
sample shading** adds `shadeSamples=false` when the property is absent. Edit it
to change the value, or delete it to restore the enabled default.

For a standalone problem or a per-problem override, start with
`polygon-init/templates/examples.tex`, save it as `statement/examples.tex`, and
place `\StatementSampleShading{false}` (or `true`) before the sample environment.
The command overrides the inherited setting for this problem only. Comments and
verbatim text do not set the control; invalid arguments are errors. Leave the
optional file absent when no customization is needed.

PDF and HTML use the same generated `.shade` / `.shade.tex` line selections.
These are derived resources, not hand-authored source files. Native Packages
preserve them. Disabling shading changes presentation only; marks remain stored.

## Existing problems

Old testlib headers continue judging normally but cannot produce the new checker
output marks. Old packages without markup render plain samples. After upgrading
the header, rerun verification and rebuild packages to obtain fresh marks.

The Statement page's **Restore defaults** dropdown lists only differing files.
Select `testlib.h`, `olymp.sty`, and/or `statements.ftl` to restore those defaults;
only selected files are overwritten. Restoring `examples.tex` removes its custom
override. Preserve intentional customizations when choosing what to restore.

PDF controls require the updated `olymp.sty`. Existing styles and templates are
not patched during rendering. When retaining a custom Contest `statements.ftl`,
add this before its problem import loop to inherit the Contest default:

```tex
\ifdefined\StatementSampleShading
\StatementSampleShading{<#if shadeSamples??><#if shadeSamples>true<#else>false</#if><#else>true</#if>}
\fi
```

The bundled default already includes this block. Keep each problem inside the
`problem` environment so local overrides do not leak to later problems. HTML
handles the control independently of the authored PDF style.
