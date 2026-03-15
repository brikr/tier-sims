import os
import json
import csv

CONFIG_FILE = "config.json"
DOCS_DIR = "docs"

CLASS_COLORS = {
    "Death Knight": "#C41E3A",
    "Demon Hunter": "#A330C9",
    "Druid": "#FF7C0A",
    "Evoker": "#33937F",
    "Hunter": "#AAD372",
    "Mage": "#3FC7EB",
    "Monk": "#00FF98",
    "Paladin": "#F48CBA",
    "Priest": "#FFFFFF",
    "Rogue": "#FFF468",
    "Shaman": "#0070DD",
    "Warlock": "#8788EE",
    "Warrior": "#C69B6D",
}

# Armor type grouping
ARMOR_TYPES = {
    "Cloth": ["Mage", "Priest", "Warlock"],
    "Leather": ["Demon Hunter", "Druid", "Monk", "Rogue"],
    "Mail": ["Evoker", "Hunter", "Shaman"],
    "Plate": ["Death Knight", "Paladin", "Warrior"],
}

# Two-word class names for parsing
TWO_WORD_CLASSES = {"Death Knight", "Demon Hunter"}


def load_config():
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)


def extract_class_name(spec_name):
    """Extract the WoW class name from a profile name like MID1_Death_Knight_Blood."""
    parts = spec_name.split("_")
    if len(parts) < 2:
        return None

    # Skip the prefix (e.g. MID1)
    remaining = parts[1:]

    # Check for two-word class names first
    if len(remaining) >= 2:
        two_word = f"{remaining[0]} {remaining[1]}"
        if two_word in TWO_WORD_CLASSES:
            return two_word

    # Single-word class name
    single = remaining[0]
    if single in CLASS_COLORS:
        return single

    return None


def get_armor_type(class_name):
    """Get the armor type for a given class name."""
    for armor_type, classes in ARMOR_TYPES.items():
        if class_name in classes:
            return armor_type
    return "Unknown"


def format_number(n):
    """Format a number with thousand separators."""
    return f"{n:,}"


def format_diff(n):
    """Format a difference value with sign and color."""
    color = "#4ade80" if n >= 0 else "#f87171"
    sign = "+" if n > 0 else ""
    return f'<span style="color: {color}">{sign}{n:,}</span>'


def generate_html(config, rows, build_info):
    """Generate the full HTML page."""
    page_title = config.get("page_title", "Tier Sims")

    # Group rows by armor type
    grouped = {}
    for armor_type in ARMOR_TYPES:
        grouped[armor_type] = []

    for row in rows:
        class_name = extract_class_name(row["Spec"])
        if class_name:
            armor_type = get_armor_type(class_name)
            grouped[armor_type].append((row, class_name))

    # Build info section
    build_info_html = ""
    if build_info:
        build_date = build_info.get("build_date", "Unknown")
        build_time = build_info.get("build_time", "Unknown")
        git_revision = build_info.get("git_revision", "")
        revision_html = git_revision
        if git_revision:
            revision_html = f'<a href="https://github.com/simulationcraft/simc/commit/{git_revision}" target="_blank" rel="noopener">{git_revision[:10]}</a>'
        build_info_html = f"""
    <div class="build-info">
      <strong>SimC Build:</strong> {build_date} {build_time} &middot; Revision: {revision_html}
    </div>"""

    # Build tables
    tables_html = ""
    for armor_type in ["Cloth", "Leather", "Mail", "Plate"]:
        armor_rows = grouped.get(armor_type, [])
        if not armor_rows:
            continue

        # Sort by 4p DPS descending
        armor_rows.sort(key=lambda x: int(x[0].get("4p", 0)), reverse=True)

        rows_html = ""
        for row, class_name in armor_rows:
            color = CLASS_COLORS.get(class_name, "#FFFFFF")
            spec_name = row["Spec"]
            dps_0p = int(row.get("0p", 0))
            dps_2p = int(row.get("2p", 0))
            dps_4p = int(row.get("4p", 0))
            # Compute differences on-the-fly if not present in CSV
            diff_0_to_2 = int(row["0p to 2p"]) if "0p to 2p" in row and row["0p to 2p"] else dps_2p - dps_0p
            diff_2_to_4 = int(row["2p to 4p"]) if "2p to 4p" in row and row["2p to 4p"] else dps_4p - dps_2p
            diff_0_to_4 = int(row["0p to 4p"]) if "0p to 4p" in row and row["0p to 4p"] else dps_4p - dps_0p

            rows_html += f"""        <tr>
          <td><a href="{spec_name}.html" target="_blank" rel="noopener" class="spec-link" style="color: {color}">{spec_name}</a></td>
          <td class="num">{format_number(dps_0p)}</td>
          <td class="num">{format_number(dps_2p)}</td>
          <td class="num">{format_number(dps_4p)}</td>
          <td class="num">{format_diff(diff_0_to_2)}</td>
          <td class="num">{format_diff(diff_2_to_4)}</td>
          <td class="num">{format_diff(diff_0_to_4)}</td>
        </tr>
"""

        tables_html += f"""
    <div class="table-section">
      <h2>{armor_type}</h2>
      <div class="table-wrapper">
        <table>
          <thead>
            <tr>
              <th>Spec</th>
              <th class="num">0p DPS</th>
              <th class="num">2p DPS</th>
              <th class="num">4p DPS</th>
              <th class="num">0p → 2p</th>
              <th class="num">2p → 4p</th>
              <th class="num">0p → 4p</th>
            </tr>
          </thead>
          <tbody>
{rows_html}          </tbody>
        </table>
      </div>
    </div>
"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="description" content="{page_title} - SimulationCraft tier set comparison results">
  <title>{page_title}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    * {{
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }}

    body {{
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
      background-color: #1a1a2e;
      color: #e0e0e0;
      line-height: 1.6;
      padding: 2rem;
      max-width: 1200px;
      margin: 0 auto;
    }}

    h1 {{
      font-size: 2rem;
      font-weight: 700;
      color: #ffffff;
      margin-bottom: 1rem;
    }}

    .disclaimer {{
      background-color: rgba(255, 255, 255, 0.05);
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 8px;
      padding: 1rem 1.25rem;
      margin-bottom: 1rem;
      font-size: 0.875rem;
      color: #a0a0b0;
    }}

    .build-info {{
      font-size: 0.85rem;
      color: #888;
      margin-bottom: 2rem;
    }}

    .build-info a {{
      color: #6d9eeb;
      text-decoration: none;
    }}

    .build-info a:hover {{
      text-decoration: underline;
    }}

    .table-section {{
      margin-bottom: 2.5rem;
    }}

    h2 {{
      font-size: 1.35rem;
      font-weight: 600;
      color: #ccccdd;
      margin-bottom: 0.75rem;
      padding-bottom: 0.35rem;
      border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    }}

    .table-wrapper {{
      overflow-x: auto;
    }}

    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 0.9rem;
    }}

    thead th {{
      text-align: left;
      padding: 0.6rem 0.75rem;
      font-weight: 600;
      color: #b0b0c0;
      border-bottom: 2px solid rgba(255, 255, 255, 0.15);
      white-space: nowrap;
    }}

    thead th.num {{
      text-align: right;
    }}

    tbody td {{
      padding: 0.5rem 0.75rem;
      border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    }}

    td.num {{
      text-align: right;
      font-variant-numeric: tabular-nums;
    }}

    tbody tr:hover {{
      background-color: rgba(255, 255, 255, 0.04);
    }}

    .spec-link {{
      text-decoration: none;
    }}

    .spec-link:hover {{
      text-decoration: underline;
    }}

    th {{
      cursor: pointer;
      user-select: none;
      position: relative;
    }}

    th:hover {{
      background-color: rgba(255, 255, 255, 0.05);
    }}

    th.sort-asc::after {{
      content: " ▲";
      font-size: 0.7em;
      opacity: 0.7;
      margin-left: 4px;
    }}

    th.sort-desc::after {{
      content: " ▼";
      font-size: 0.7em;
      opacity: 0.7;
      margin-left: 4px;
    }}
  </style>
</head>
<body>
  <header>
    <h1>{page_title}</h1>
    <div class="disclaimer">
      ⚠️ Some specs or tier sets may not be fully implemented in SimulationCraft.
    </div>
{build_info_html}
  </header>
  <main>
{tables_html}
  </main>
  <script>
    document.addEventListener('DOMContentLoaded', function() {{
      const getCellValue = (tr, idx) => tr.children[idx].innerText || tr.children[idx].textContent;
      
      const parseValue = (v) => {{
        const cleanStr = v.replace(/[,+\\s]/g, '').trim();
        const num = parseFloat(cleanStr);
        return isNaN(num) ? v : num;
      }};

      const comparer = (idx, asc) => (a, b) => {{
        const v1 = parseValue(getCellValue(asc ? a : b, idx));
        const v2 = parseValue(getCellValue(asc ? b : a, idx));
        if (v1 !== '' && v2 !== '' && !isNaN(v1) && !isNaN(v2)) {{
          return v1 - v2;
        }}
        return v1.toString().localeCompare(v2);
      }};

      document.querySelectorAll('th').forEach(th => th.addEventListener('click', (() => {{
        const table = th.closest('table');
        const tbody = table.querySelector('tbody');
        if (!tbody) return;
        
        table.querySelectorAll('th').forEach(t => t.classList.remove('sort-asc', 'sort-desc'));
        
        let isAsc;
        if (th.dataset.sortAsc === undefined) {{
          isAsc = !th.classList.contains('num');
        }} else {{
          isAsc = th.dataset.sortAsc !== 'true';
        }}
        th.dataset.sortAsc = isAsc;
        th.classList.add(isAsc ? 'sort-asc' : 'sort-desc');

        Array.from(tbody.querySelectorAll('tr'))
          .sort(comparer(Array.from(th.parentNode.children).indexOf(th), isAsc))
          .forEach(tr => tbody.appendChild(tr));
      }})));
    }});
  </script>
</body>
</html>
"""
    return html


def main():
    config = load_config()

    # Read CSV
    csv_path = os.path.join(DOCS_DIR, "tier_sims.csv")
    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} not found. Run simulations first.")
        return

    rows = []
    with open(csv_path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

    # Read build info
    build_info = {}
    build_info_path = os.path.join(DOCS_DIR, "build_info.json")
    if os.path.exists(build_info_path):
        with open(build_info_path, "r") as f:
            build_info = json.load(f)

    # Generate HTML
    html = generate_html(config, rows, build_info)

    # Write to docs/index.html
    output_path = os.path.join(DOCS_DIR, "index.html")
    with open(output_path, "w") as f:
        f.write(html)

    print(f"Generated {output_path}")


if __name__ == "__main__":
    main()
