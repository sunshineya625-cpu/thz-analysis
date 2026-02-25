from streamlit.testing.v1 import AppTest
from pathlib import Path

print("Loading test...")
at = AppTest.from_file(r"d:\Google Antigravity\work-place\thz-analysis\app.py")

print("Running initial app...")
at.run(timeout=10)

print("Uploading data files...")
# Get two files from the Data test dir
# 183710 is 70K, 183720 is 70K, 183737 is 70K
fpaths = [
    r"D:\Google Antigravity\work-place\Data test\TNS 3_20260220183710_average.txt",
    r"D:\Google Antigravity\work-place\Data test\TNS 3_20260220183720_average.txt",
    r"D:\Google Antigravity\work-place\Data test\TNS 3_20260220183737_average.txt"
]

class FakeUpload:
    def __init__(self, p):
        self.name = Path(p).name
        self.data = open(p, "rb").read()
    def getvalue(self):
        return self.data

at.sidebar.file_uploader[0].set_value([FakeUpload(p) for p in fpaths])
at.run(timeout=30)

print(f"Loaded {len(at.session_state.files)} files")
print(f"Num averaged files: {len(at.session_state.averaged_files)}")

if len(at.session_state.averaged_files) > 0:
    avg0 = at.session_state.averaged_files[0]
    print(f"Initial Average 70K Amp at idx 500: {avg0['amp'][500]:.6e}")

print("Switching to ROI tab...")
# Switch to tab 1 (ROI)
# In apptest, tabs aren't interactive directly, we interact with widgets.
# Radio for View mode has key 'roi_view_mode'
view_radio = at.radio(key="roi_view_mode")
print(f"View radio found: {view_radio.value}")
view_radio.set_value("Raw scans (select/exclude) 原始扫描").run()

# Look for checkboxes
checkboxes = [cb for cb in at.checkbox if cb.key and cb.key.startswith("roi_excl_")]
print(f"Found {len(checkboxes)} exclusion checkboxes")

if checkboxes:
    # Uncheck the first one
    print(f"Unchecking {checkboxes[0].key}...")
    checkboxes[0].uncheck().run()
    
    # Click the Re-average button
    btn = at.button(key="roi_reavg_btn")
    print(f"Clicking button: {btn.label}")
    btn.click().run()
    
    avg_after = at.session_state.averaged_files[0]
    print(f"Excluded scans in state: {at.session_state.excluded_scans}")
    print(f"After re-average Amp at idx 500: {avg_after['amp'][500]:.6e}")
else:
    print("No checkboxes found!")

print("Checking sidebar config reload state...")
# If need_reload gets triggered, st.session_state.averaged_files would be re-calculated 
# using the FULL list of files without exclusions.
