"""
OS Nexus Lite - Interactive Operating System Simulator
Topics: Virtual memory, Demand paging, Page faults, File allocation,
        File access, Directory structure, Disk scheduling, Head movement.
Run with:  python -m streamlit run app.py
"""

import copy

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

# =====================================================================
# SECTION 1: HELPER FUNCTIONS (pure logic, no Streamlit code)
# =====================================================================


def parse_numbers(text, name):
    """Turn '1, 2, 3' into [1, 2, 3]. Raises ValueError with a friendly message."""
    parts = [p for p in text.replace(",", " ").split() if p]
    if not parts:
        raise ValueError(f"Please enter at least one number for {name}.")
    numbers = []
    for p in parts:
        if not p.isdigit():
            raise ValueError(f"'{p}' is not a valid non-negative whole number in {name}.")
        numbers.append(int(p))
    return numbers


# ---------------- Page replacement (demand paging) ----------------


def simulate_paging(pages, frame_count, algorithm):
    """
    Simulate demand paging with FIFO or LRU.
    frames   : fixed slots (None = empty slot)
    order    : pages in memory, oldest/least-recently-used first
    FIFO     : order changes only when a page is loaded
    LRU      : order also changes on every hit (page moves to the end)
    """
    frames = [None] * frame_count
    order = []
    rows = []
    faults = 0
    hits = 0

    for step, page in enumerate(pages, start=1):
        replaced = "-"
        if page in frames:
            result = "Hit"
            hits += 1
            if algorithm == "LRU":
                order.remove(page)
                order.append(page)  # now most recently used
        else:
            result = "Fault"
            faults += 1
            if None in frames:  # free frame available
                slot = frames.index(None)
            else:  # memory full -> pick a victim
                victim = order.pop(0)
                slot = frames.index(victim)
                replaced = str(victim)
            frames[slot] = page
            order.append(page)

        row = {"Step": step, "Page": str(page)}
        for i in range(frame_count):
            row[f"Frame {i + 1}"] = "-" if frames[i] is None else str(frames[i])
        row["Result"] = result
        row["Replaced"] = replaced
        rows.append(row)

    return rows, faults, hits


# ---------------- Virtual memory address translation ----------------

# Sample page table: page number -> frame number (None = page is on disk)
SAMPLE_PAGE_TABLE = {0: 5, 1: 2, 2: None, 3: 7, 4: None, 5: 0, 6: None, 7: 3}


# ---------------- File allocation ----------------

DISK_SIZE = 32
USED_BLOCKS = [2, 3, 7, 8, 12, 13, 20, 25, 26]  # blocks used by "other" files


def free_block_list():
    return [b for b in range(DISK_SIZE) if b not in USED_BLOCKS]


def allocate_contiguous(size):
    """First-fit: find `size` free blocks sitting next to each other."""
    run = []
    for b in range(DISK_SIZE):
        if b in USED_BLOCKS:
            run = []
        else:
            run.append(b)
            if len(run) == size:
                return run
    return None


def allocate_linked(size):
    """Take any `size` free blocks (they can be scattered)."""
    free = free_block_list()
    if len(free) < size:
        return None
    return free[:size]


def allocate_indexed(size):
    """One free block becomes the index block, next `size` free blocks hold data."""
    free = free_block_list()
    if len(free) < size + 1:
        return None, None
    return free[0], free[1:size + 1]


def disk_grid_html(allocated, index_block=None):
    """Draw the simulated disk as a grid of colored cells."""
    cells = ""
    for b in range(DISK_SIZE):
        if b == index_block:
            color, tip = "#f4a261", "index"
        elif b in allocated:
            color, tip = "#2a9d8f", "file"
        elif b in USED_BLOCKS:
            color, tip = "#adb5bd", "used"
        else:
            color, tip = "#f8f9fa", "free"
        cells += (
            f"<div style='background:{color};color:#111;border:1px solid #666;"
            f"border-radius:6px;padding:6px 0;text-align:center;font-size:13px'>"
            f"<b>{b}</b><br><span style='font-size:10px'>{tip}</span></div>"
        )
    return (
        "<div style='display:grid;grid-template-columns:repeat(8,1fr);gap:4px;"
        f"max-width:560px'>{cells}</div>"
    )


# ---------------- File access ----------------

STUDENTS = ["Aarav", "Diya", "Kabir", "Meera", "Rohan", "Sneha", "Vikram", "Anaya", "Ishaan", "Tara"]
RECORDS = {i + 1: f"Roll {i + 1}: {name}" for i, name in enumerate(STUDENTS)}
RECORD_SIZE = 20  # every record takes 20 bytes
# Index table: record number -> disk block where that record is stored
INDEX_TABLE = {1: 9, 2: 3, 3: 14, 4: 7, 5: 21, 6: 2, 7: 18, 8: 11, 9: 5, 10: 16}


# ---------------- Directory structure ----------------


def sample_tree():
    """Folders are dictionaries, files are None."""
    return {
        "Documents": {"resume.pdf": None, "Projects": {"os_project.py": None}},
        "Pictures": {"trip.jpg": None},
        "readme.txt": None,
    }


def folder_paths(tree, path="/"):
    """List every folder path, e.g. ['/', '/Documents', '/Documents/Projects']."""
    paths = [path]
    for name, child in tree.items():
        if child is not None:
            child_path = "/" + name if path == "/" else path + "/" + name
            paths += folder_paths(child, child_path)
    return paths


def get_folder(tree, path):
    node = tree
    for part in [p for p in path.split("/") if p]:
        node = node[part]
    return node


def tree_lines(node, prefix=""):
    """Convert nested dictionary to text lines like a 'tree' command."""
    lines = []
    items = list(node.items())
    for i, (name, child) in enumerate(items):
        last = i == len(items) - 1
        label = name + "/" if child is not None else name
        lines.append(prefix + ("└── " if last else "├── ") + label)
        if child is not None:
            lines += tree_lines(child, prefix + ("    " if last else "│   "))
    return lines


# ---------------- Disk scheduling ----------------


def fcfs(head, reqs):
    order = list(reqs)
    return order, [head] + order, 0


def sstf(head, reqs):
    remaining = list(reqs)
    current = head
    order = []
    while remaining:
        nearest = min(remaining, key=lambda r: abs(r - current))
        order.append(nearest)
        remaining.remove(nearest)
        current = nearest
    return order, [head] + order, 0


def scan(head, reqs, low, high, direction):
    """Go to one end serving requests, then reverse and serve the rest."""
    if direction == "Right":
        first = sorted([r for r in reqs if r >= head])
        second = sorted([r for r in reqs if r < head], reverse=True)
        boundary = high
    else:
        first = sorted([r for r in reqs if r <= head], reverse=True)
        second = sorted([r for r in reqs if r > head])
        boundary = low
    path = [head] + first
    if path[-1] != boundary:
        path.append(boundary)  # SCAN always travels to the disk end
    path += second
    return first + second, path, 0


def cscan(head, reqs, low, high, direction):
    """Go to one end serving requests, jump to the other end, continue same direction."""
    if direction == "Right":
        first = sorted([r for r in reqs if r >= head])
        second = sorted([r for r in reqs if r < head])
        boundary, other_end = high, low
    else:
        first = sorted([r for r in reqs if r <= head], reverse=True)
        second = sorted([r for r in reqs if r > head], reverse=True)
        boundary, other_end = low, high
    path = [head] + first
    if path[-1] != boundary:
        path.append(boundary)
    jump = 0
    if second:  # jump only if requests are waiting on the other side
        path.append(other_end)
        jump = abs(boundary - other_end)
        path += second
    return first + second, path, jump


def run_algorithm(name, head, reqs, low, high, direction, count_jump=True):
    """Run one algorithm; returns (service order, head path, total movement)."""
    if name == "FCFS":
        order, path, jump = fcfs(head, reqs)
    elif name == "SSTF":
        order, path, jump = sstf(head, reqs)
    elif name == "SCAN":
        order, path, jump = scan(head, reqs, low, high, direction)
    else:
        order, path, jump = cscan(head, reqs, low, high, direction)
    total = sum(abs(path[i + 1] - path[i]) for i in range(len(path) - 1))
    if not count_jump:
        total -= jump
    return order, path, total


def draw_head_graph(path, title):
    """Head position (x) against service step (y, top to bottom)."""
    fig, ax = plt.subplots(figsize=(8, 4))
    steps = list(range(len(path)))
    ax.plot(path, steps, marker="o", color="#2a9d8f")
    for s, c in zip(steps, path):
        ax.annotate(str(c), (c, s), textcoords="offset points", xytext=(0, 7), ha="center", fontsize=8)
    ax.invert_yaxis()
    ax.set_xlabel("Cylinder number")
    ax.set_ylabel("Step")
    ax.set_title(title)
    ax.grid(True, alpha=0.3)
    return fig


# =====================================================================
# SECTION 2: STREAMLIT PAGES
# =====================================================================


def page_home():
    st.title("🖥️ OS Nexus Lite")
    st.subheader("Interactive Operating System Simulator")
    st.write(
        "OS Nexus Lite is a mini project that lets you *see* how an operating system "
        "manages memory, files and the disk. Pick a topic from the sidebar, enter your "
        "own inputs (or use the ready-made samples) and watch the simulation step by step."
    )
    st.markdown("### Topics covered")
    topics = pd.DataFrame(
        {
            "No.": range(1, 9),
            "Topic": [
                "Virtual memory",
                "Demand paging",
                "Page faults",
                "File allocation methods",
                "File access methods",
                "Directory structure",
                "Disk scheduling algorithms",
                "Disk head movement calculation",
            ],
            "Where to find it": [
                "Virtual Memory & Paging (Address Translation tab)",
                "Virtual Memory & Paging (Simulation tab)",
                "Virtual Memory & Paging (Simulation tab)",
                "File Allocation",
                "File Access",
                "Directory Structure",
                "Disk Scheduling",
                "Disk Scheduling",
            ],
        }
    ).set_index("No.")
    st.dataframe(topics)
    st.markdown("### Project information")
    st.write(
        "- **Language:** Python  \n"
        "- **Interface:** Streamlit web dashboard  \n"
        "- **Graphs:** Matplotlib  \n"
        "- **Data storage:** Only Python lists, dictionaries and session state (no database)  \n"
        "- **Safety:** Everything is simulated. Your real files are never touched."
    )


def page_memory():
    st.header("🧠 Virtual Memory, Demand Paging & Page Faults")
    with st.expander("How it works", expanded=True):
        st.write(
            "**Virtual memory** lets a program use more memory than the RAM available by keeping "
            "only some of its pages in RAM and the rest on disk.  \n"
            "**Demand paging** loads a page into a RAM frame only when the program asks for it.  \n"
            "**Page fault** happens when the requested page is not in RAM. The OS loads it from disk, "
            "and if all frames are full it must replace one page.  \n"
            "- **FIFO** replaces the page that has been in memory the longest.  \n"
            "- **LRU** replaces the page that was used least recently."
        )

    tab1, tab2 = st.tabs(["Page Replacement Simulation", "Address Translation"])

    with tab1:
        ref_text = st.text_input(
            "Page reference string (comma separated)",
            "7, 0, 1, 2, 0, 3, 0, 4, 2, 3, 0, 3, 2, 1, 2, 0, 1, 7, 0, 1",
        )
        frame_count = int(st.number_input("Number of frames", min_value=1, max_value=10, value=3, step=1))
        algorithm = st.radio("Page replacement algorithm", ["FIFO", "LRU"], horizontal=True)

        if st.button("Run simulation"):
            try:
                pages = parse_numbers(ref_text, "the reference string")
            except ValueError as error:
                st.error(str(error))
                return

            rows, faults, hits = simulate_paging(pages, frame_count, algorithm)
            total = len(pages)

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total requests", total)
            c2.metric("Page faults", faults)
            c3.metric("Page hits", hits)
            c4.metric("Hit ratio", f"{hits / total * 100:.1f}%")

            st.markdown(f"#### {algorithm}: frame contents after every request")
            df = pd.DataFrame(rows).set_index("Step")

            def color_rows(row):
                color = "background-color: #f8d7da; color: #111" if row["Result"] == "Fault" else "background-color: #d1e7dd; color: #111"
                return [color] * len(row)

            st.dataframe(df.style.apply(color_rows, axis=1))
            st.caption("Red rows = page fault, green rows = page hit. '-' means the frame is still empty.")

            # Compare both algorithms on the same input
            _, fifo_faults, fifo_hits = simulate_paging(pages, frame_count, "FIFO")
            _, lru_faults, lru_hits = simulate_paging(pages, frame_count, "LRU")
            st.markdown("#### FIFO vs LRU on the same input")
            compare = pd.DataFrame(
                {
                    "Algorithm": ["FIFO", "LRU"],
                    "Page faults": [fifo_faults, lru_faults],
                    "Page hits": [fifo_hits, lru_hits],
                    "Hit ratio (%)": [round(fifo_hits / total * 100, 1), round(lru_hits / total * 100, 1)],
                }
            ).set_index("Algorithm")
            st.dataframe(compare)

            st.info(
                f"With {frame_count} frame(s), {algorithm} caused {faults} page faults and {hits} hits "
                f"out of {total} requests (hit ratio {hits / total * 100:.1f}%)."
            )

    with tab2:
        st.write(
            "A virtual (logical) address is split into a **page number** and an **offset**. "
            "The page table tells which RAM frame holds that page. If the page is not in RAM, a page fault occurs."
        )
        page_size = int(st.number_input("Page size (bytes)", min_value=1, max_value=65536, value=1024, step=1))
        max_address = len(SAMPLE_PAGE_TABLE) * page_size - 1
        address = int(
            st.number_input(
                f"Logical address (0 to {max_address})", min_value=0, max_value=max_address, value=min(2500, max_address), step=1
            )
        )
        table_df = pd.DataFrame(
            {
                "Page": list(SAMPLE_PAGE_TABLE.keys()),
                "Frame": ["On disk" if f is None else str(f) for f in SAMPLE_PAGE_TABLE.values()],
            }
        ).set_index("Page")
        st.markdown("Sample page table (8 virtual pages):")
        st.dataframe(table_df)

        if st.button("Translate address"):
            page_no = address // page_size
            offset = address % page_size
            st.write(f"Page number = {address} // {page_size} = **{page_no}**, offset = {address} % {page_size} = **{offset}**")
            frame = SAMPLE_PAGE_TABLE[page_no]
            if frame is None:
                st.error(
                    f"Page fault! Page {page_no} is not in RAM. The OS loads it from disk into a free frame "
                    "(demand paging) and then the instruction is restarted."
                )
            else:
                physical = frame * page_size + offset
                st.success(
                    f"Page {page_no} is in frame {frame}. Physical address = {frame} × {page_size} + {offset} = **{physical}**"
                )


def page_allocation():
    st.header("💾 File Allocation Methods")
    with st.expander("How it works", expanded=True):
        st.write(
            "The disk is divided into equal blocks. A file needs `size` blocks. "
            f"This simulated disk has {DISK_SIZE} blocks and some are already used by other files (grey).  \n"
            "- **Contiguous:** all blocks of the file are next to each other. Fast, but needs one big free gap (external fragmentation).  \n"
            "- **Linked:** blocks can be anywhere; each block stores a pointer to the next one. No fragmentation, but only sequential access is fast.  \n"
            "- **Indexed:** one special index block holds the addresses of all data blocks. Supports direct access, but costs one extra block."
        )

    file_name = st.text_input("File name", "notes.txt")
    size = int(st.number_input("File size (in blocks)", min_value=1, max_value=30, value=5, step=1))
    method = st.radio("Allocation method", ["Contiguous", "Linked", "Indexed"], horizontal=True)

    if st.button("Allocate file"):
        if not file_name.strip():
            st.error("Please enter a file name.")
            return
        name = file_name.strip()
        index_block = None

        if method == "Contiguous":
            blocks = allocate_contiguous(size)
            if blocks is None:
                st.error(
                    f"Cannot allocate '{name}': there is no run of {size} free blocks in a row, "
                    f"even though {len(free_block_list())} blocks are free in total. This is external fragmentation."
                )
                st.markdown(disk_grid_html([]), unsafe_allow_html=True)
                return
            st.success(f"'{name}' stored in blocks {blocks[0]} to {blocks[-1]} (start = {blocks[0]}, length = {size}).")
        elif method == "Linked":
            blocks = allocate_linked(size)
            if blocks is None:
                st.error(f"Not enough free blocks. Needed {size}, only {len(free_block_list())} free.")
                return
            chain = " → ".join(str(b) for b in blocks) + " → NULL"
            st.success(f"'{name}' stored in blocks {blocks}.")
            st.write(f"Pointer chain: **{chain}**")
        else:
            index_block, blocks = allocate_indexed(size)
            if blocks is None:
                st.error(f"Not enough free blocks. Needed {size + 1} (including the index block), only {len(free_block_list())} free.")
                return
            st.success(f"'{name}' uses block {index_block} as its index block and blocks {blocks} for data.")
            index_df = pd.DataFrame({"Index entry": range(size), "Points to block": blocks}).set_index("Index entry")
            st.write(f"Index table stored in block {index_block}:")
            st.dataframe(index_df)

        st.markdown("**Simulated disk** (green = this file, orange = index block, grey = used by other files, white = free)")
        st.markdown(disk_grid_html(blocks, index_block), unsafe_allow_html=True)


def page_access():
    st.header("📂 File Access Methods")
    with st.expander("How it works", expanded=True):
        st.write(
            f"The sample file has {len(RECORDS)} records, each {RECORD_SIZE} bytes.  \n"
            "- **Sequential:** start at record 1 and read one record after another until the wanted one is reached.  \n"
            "- **Direct:** jump straight to the record using its position: offset = (record number − 1) × record size.  \n"
            "- **Indexed:** look up the record number in an index table to get its disk block, then read that block."
        )
    st.markdown("Sample file:")
    st.dataframe(pd.DataFrame({"Record no.": list(RECORDS.keys()), "Data": list(RECORDS.values())}).set_index("Record no."))

    method = st.radio("Access method", ["Sequential", "Direct", "Indexed"], horizontal=True)
    record_no = int(st.number_input("Record number to access", min_value=1, max_value=len(RECORDS), value=7, step=1))

    if st.button("Access record"):
        if method == "Sequential":
            st.write("Reading from the beginning:")
            for n in range(1, record_no + 1):
                st.write(f"- Read record {n}" + (" ← found!" if n == record_no else ""))
            reads = record_no
            how = f"Sequential access had to read **{reads}** record(s) to reach record {record_no}."
        elif method == "Direct":
            offset = (record_no - 1) * RECORD_SIZE
            st.write(f"Offset = ({record_no} − 1) × {RECORD_SIZE} = **{offset} bytes**. The system jumps straight there.")
            how = "Direct access read only **1** record, no matter which record was asked for."
        else:
            block = INDEX_TABLE[record_no]
            st.write(f"Index table lookup: record {record_no} → disk block **{block}**. Now read that block.")
            how = "Indexed access did **1** index lookup and **1** block read."
        st.success(f"Record {record_no} = {RECORDS[record_no]}")
        st.info(how)

    with st.expander("Show the index table used by Indexed access"):
        st.dataframe(pd.DataFrame({"Record no.": list(INDEX_TABLE.keys()), "Disk block": list(INDEX_TABLE.values())}).set_index("Record no."))


def page_directory():
    st.header("🗂️ Directory Structure")
    with st.expander("How it works", expanded=True):
        st.write(
            "A directory keeps track of the files in a file system.  \n"
            "- **Single-level:** one directory holds every file. Simple, but file names must all be unique and it gets messy.  \n"
            "- **Tree-structured:** folders can contain files and other folders. Files are found using a path such as `/Documents/Projects/os_project.py`."
        )

    if "single_dir" not in st.session_state:
        st.session_state.single_dir = ["notes.txt", "photo.jpg", "report.docx"]
    if "tree_dir" not in st.session_state:
        st.session_state.tree_dir = sample_tree()

    tab1, tab2 = st.tabs(["Single-level", "Tree-structured"])

    with tab1:
        new_name = st.text_input("New file name", key="single_name")
        c1, c2 = st.columns(2)
        if c1.button("Add file", key="single_add"):
            name = new_name.strip()
            if not name:
                st.error("Please enter a file name.")
            elif "/" in name:
                st.error("A single-level directory has no folders, so '/' is not allowed.")
            elif name in st.session_state.single_dir:
                st.error(f"'{name}' already exists. File names must be unique in a single-level directory.")
            else:
                st.session_state.single_dir.append(name)
                st.success(f"Added '{name}'.")
        if c2.button("Reset sample", key="single_reset"):
            st.session_state.single_dir = ["notes.txt", "photo.jpg", "report.docx"]
        st.code("Root directory\n" + "\n".join("├── " + f for f in st.session_state.single_dir), language=None)

    with tab2:
        parent = st.selectbox("Create inside folder", folder_paths(st.session_state.tree_dir))
        item_type = st.radio("Type", ["File", "Folder"], horizontal=True)
        item_name = st.text_input("Name", key="tree_name")
        c1, c2 = st.columns(2)
        if c1.button("Add to tree", key="tree_add"):
            name = item_name.strip()
            folder = get_folder(st.session_state.tree_dir, parent)
            if not name:
                st.error("Please enter a name.")
            elif "/" in name:
                st.error("Names cannot contain '/'.")
            elif name in folder:
                st.error(f"'{name}' already exists in {parent}.")
            else:
                folder[name] = {} if item_type == "Folder" else None
                st.success(f"Added {item_type.lower()} '{name}' inside {parent}.")
        if c2.button("Reset sample", key="tree_reset"):
            st.session_state.tree_dir = sample_tree()
        st.code("/\n" + "\n".join(tree_lines(st.session_state.tree_dir)), language=None)
        st.caption("Names ending with '/' are folders.")


def page_disk():
    st.header("🔄 Disk Scheduling & Head Movement")
    with st.expander("How it works", expanded=True):
        st.write(
            "The disk head must move to each requested cylinder. Different algorithms choose the order differently. "
            "**Total head movement** = sum of the distances the head travels between consecutive positions.  \n"
            "- **FCFS:** serve requests in the order they arrived.  \n"
            "- **SSTF:** always serve the request closest to the current head position.  \n"
            "- **SCAN (elevator):** move in one direction to the disk end serving requests, then reverse.  \n"
            "- **C-SCAN:** move in one direction to the end, jump back to the other end, and continue in the same direction."
        )

    c1, c2, c3 = st.columns(3)
    head = int(c1.number_input("Initial head position", min_value=0, value=53, step=1))
    low = int(c2.number_input("Lowest cylinder", min_value=0, value=0, step=1))
    high = int(c3.number_input("Highest cylinder", min_value=1, value=199, step=1))
    req_text = st.text_input("Pending requests (comma separated)", "98, 183, 37, 122, 14, 124, 65, 67")
    algorithm = st.selectbox("Algorithm", ["FCFS", "SSTF", "SCAN", "C-SCAN"])
    direction = st.radio("Initial direction (used by SCAN and C-SCAN)", ["Right", "Left"], horizontal=True)
    count_jump = st.checkbox("Count the C-SCAN return jump in total head movement", value=True)

    if st.button("Run scheduling"):
        try:
            reqs = parse_numbers(req_text, "the request list")
        except ValueError as error:
            st.error(str(error))
            return
        if low >= high:
            st.error("The lowest cylinder must be smaller than the highest cylinder.")
            return
        if not (low <= head <= high):
            st.error(f"The head position must be between {low} and {high}.")
            return
        bad = [r for r in reqs if r < low or r > high]
        if bad:
            st.error(f"These requests are outside the cylinder range {low}-{high}: {bad}")
            return

        order, path, total = run_algorithm(algorithm, head, reqs, low, high, direction, count_jump)

        st.markdown(f"### Result: {algorithm}")
        st.write("**Service order:** " + " → ".join(str(r) for r in order))
        st.write("**Head path:** " + " → ".join(str(p) for p in path))
        steps = " + ".join(str(abs(path[i + 1] - path[i])) for i in range(len(path) - 1))
        st.write(f"**Calculation:** {steps} = **{total}**")
        st.metric("Total head movement", f"{total} cylinders")
        fig = draw_head_graph(path, f"{algorithm} head movement")
        st.pyplot(fig)
        plt.close(fig)

        # Plain-English explanation
        text = f"The head started at cylinder {head} and served the requests in the order {order}. "
        if algorithm == "FCFS":
            text += "FCFS is fair because it follows arrival order, but the head may swing back and forth a lot."
        elif algorithm == "SSTF":
            text += "SSTF picked the closest pending request each time, which keeps movement low but can starve far-away requests."
        elif algorithm == "SCAN":
            text += (
                f"The head moved {direction.lower()} to the disk end ({high if direction == 'Right' else low}), "
                "then reversed to serve the remaining requests."
            )
        else:
            text += (
                f"The head moved {direction.lower()} to the disk end, jumped to the other end and continued "
                f"in the same direction. The return jump was {'counted' if count_jump else 'not counted'}."
            )
        text += f" Total head movement = {total} cylinders."
        st.info(text)

        # Compare all four algorithms
        names = ["FCFS", "SSTF", "SCAN", "C-SCAN"]
        totals = [run_algorithm(n, head, reqs, low, high, direction, count_jump)[2] for n in names]
        st.markdown("#### Comparison of all four algorithms (same input)")
        st.dataframe(pd.DataFrame({"Algorithm": names, "Total head movement": totals}).set_index("Algorithm"))
        st.bar_chart(pd.DataFrame({"Total head movement": totals}, index=names))


# =====================================================================
# SECTION 3: MAIN - sidebar navigation
# =====================================================================


def main():
    st.set_page_config(page_title="OS Nexus Lite", page_icon="🖥️", layout="wide")
    st.sidebar.title("🖥️ OS Nexus Lite")
    pages = {
        "🏠 Home & Project Info": page_home,
        "🧠 Virtual Memory & Paging": page_memory,
        "💾 File Allocation": page_allocation,
        "📂 File Access": page_access,
        "🗂️ Directory Structure": page_directory,
        "🔄 Disk Scheduling": page_disk,
    }
    choice = st.sidebar.radio("Choose a topic", list(pages.keys()))
    pages[choice]()
    st.sidebar.caption("All simulations are in memory. Your real files are never changed.")


if __name__ == "__main__":
    main()
