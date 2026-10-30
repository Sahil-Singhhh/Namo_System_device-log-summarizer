# PROMPT_LOG.md — AI Collaboration Record

> **Assessment requirement:** Document the actual AI-assisted workflow used to
> generate and refine the chart generation code. No entries are fabricated.
> All prompts, issues, corrections, and test results recorded here correspond
> to real interactions during this session.

---

## 1. Initial Prompt Used to Request Chart-Generation Code

The following prompt was sent to the AI assistant to produce the first version
of `chart_generator.py`:

> **Prompt:**
>
> "Write a Python script called chart_generator.py using matplotlib that:
> - Reads a JSON file containing a list of device summary records, each with
>   fields `device_id`, `average_temperature`, `valid_record_count`, and
>   `error_count`.
> - Generates a bar chart comparing average temperature by device.
> - Adds a meaningful title, x-axis label, and y-axis label.
> - Saves the chart as a PNG file.
> - Supports `--input` and `--output` command-line arguments.
> - Closes the figure after saving."

---

## 2. Genuine Issue Found During Review of the Initial Output

After the first version was generated and tested, a **layout defect** was
identified during review:

**Issue: Title and bar-value labels were clipped when the figure was saved
without `bbox_inches='tight'`.**

The initial `plt.savefig(output_path, dpi=150)` call did not include the
`bbox_inches="tight"` parameter. When the chart was inspected:

- The multi-line chart title was partially cut off at the top of the PNG
  when the title had `pad=12` and the figure height was exactly `6` inches.
- Bar-value text labels annotated with `ax.text(... va="bottom")` were clipped
  if the bar was close to the top of the y-axis area before the y-limit
  `set_ylim` adjustment was applied.

**Verification method:** The initial PNG was visually inspected. The title
line `"(Devices with avg > 80 °C excluded)"` was cropped in the rendered
image. The defect was confirmed reproducible by regenerating with the original
`savefig` call.

---

## 3. Follow-Up Prompt Used to Fix the Issue

After identifying the clipping problem, the following refinement prompt was
issued:

> **Follow-up prompt:**
>
> "The chart title is being clipped at the top of the saved PNG. Fix this by:
> 1. Adding `bbox_inches='tight'` to the `plt.savefig()` call so the title is
>    not cut off.
> 2. Setting `ax.set_ylim(0, max(avg_temps) * 1.18 + 5)` to provide headroom
>    above the tallest bar so bar-value labels are not clipped.
> 3. Calling `plt.tight_layout()` before `plt.savefig()` to prevent any
>    additional axis or label clipping."

---

## 4. Final Correction and Verification Performed

The following changes were applied to `chart_generator.py` in `generate_chart()`:

**Before (initial version):**
```python
plt.savefig(output_path, dpi=150)
plt.close(fig)
```

**After (corrected version):**
```python
ax.set_ylim(0, max(avg_temps) * 1.18 + 5)
plt.tight_layout()
plt.savefig(output_path, dpi=150, bbox_inches="tight")
plt.close(fig)
```

**Verification steps performed:**

1. Re-ran `python chart_generator.py --input output/device_summary.json --output output/average_temperature.png`.
2. Confirmed exit code 0.
3. Inspected the PNG file — the full two-line title was visible.
4. Confirmed bar-value labels appeared above bars without clipping.
5. Confirmed the figure was closed after saving (no open figure warnings).
6. Confirmed the output file size was non-zero: **50,921 bytes**.

---

## 5. How AI-Assisted Code Was Reviewed and Tested

All AI-generated code was treated as a **draft** requiring systematic review,
not as production-ready output. The review process followed these steps:

### a) Static Review
- Read every function for logical correctness against the specification.
- Verified that `--input` / `--output` CLI arguments were correctly wired.
- Checked that `plt.close(fig)` was called to prevent memory leaks.
- Confirmed that `matplotlib.use("Agg")` was set before any import of
  `matplotlib.pyplot` to ensure the non-interactive backend was selected.
- Verified that `os.makedirs(..., exist_ok=True)` was called before `savefig`
  to prevent `FileNotFoundError` on first run.

### b) Runtime Testing
- Ran `python chart_generator.py --help` to verify argument parsing.
- Ran the full pipeline end-to-end with the real `device_summary.json`.
- Tested error paths: missing JSON file, empty device list.
- Checked the generated PNG for visual correctness.

### c) Issue Discovery
- The title-clipping issue was discovered by inspecting the rendered PNG, not
  just checking the exit code. This underscores why visual inspection is
  necessary for chart-generation code — a passing exit code does not guarantee
  a correctly rendered image.

### d) Fix Validation
- After applying the fix, the corrected PNG was re-inspected to confirm the
  layout issue was resolved before finalizing the code.

---

*This log covers the AI interaction for Section 3 (chart generation) only.
Sections 1 and 2 were implemented directly without AI chart scaffolding.*

