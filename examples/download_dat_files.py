from acdesign.airfoils.airfoil import Airfoil
from acdesign.airfoils.polar import available_sections
from pathlib import Path
sections = available_sections()

for section in sections:
    try:
        airfoil = Airfoil.parse_selig(Path(f"src/data/uiuc/{section}.dat"))
    except Exception as e:
        print(f"could not parse {section}: {e}")

