# OS Nexus Lite - Report Material

## 1. Run it on Windows

Put `app.py` and `requirements.txt` in one folder (for example `C:\osnexus`). Open Command Prompt:

```
cd C:\osnexus
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

The browser opens at http://localhost:8501. Stop the app with Ctrl + C in the Command Prompt.

## 2. Sample inputs and expected outputs

**Virtual Memory & Paging** (defaults are pre-filled)
- Input: reference string `7, 0, 1, 2, 0, 3, 0, 4, 2, 3, 0, 3, 2, 1, 2, 0, 1, 7, 0, 1`, 3 frames.
- FIFO: 15 faults, 5 hits, hit ratio 25.0%.
- LRU: 12 faults, 8 hits, hit ratio 40.0%.
- Small example: `1, 2, 3, 1, 4, 2` with 3 frames gives FIFO 4 faults / 2 hits and LRU 5 faults / 1 hit.
- Address Translation tab: page size 1024, address 2500 gives page 2, offset 452, page fault (page 2 is on disk). Address 1500 gives page 1, offset 476, frame 2, physical address 2524.

**File Allocation** (file `notes.txt`, 5 blocks)
- Contiguous: blocks 14 to 18.
- Linked: blocks 0 → 1 → 4 → 5 → 6 → NULL.
- Indexed: index block 0, data blocks 1, 4, 5, 6, 9.
- Try size 7 with Contiguous: it fails with an external fragmentation message (23 blocks free, but no 7 in a row).

**File Access** (record 7)
- Sequential: reads records 1 to 7 (7 reads).
- Direct: offset = (7 − 1) × 20 = 120 bytes (1 read).
- Indexed: index table gives disk block 18 (1 lookup + 1 read).
- Result in all three: `Roll 7: Vikram`.

**Directory Structure**
- Single-level: add `lab.txt`; adding it again shows a "must be unique" error.
- Tree: choose `/Documents`, type Folder, name `Labs`; it appears under Documents. Folders end with `/`.

**Disk Scheduling** (head 53, range 0 to 199, requests `98, 183, 37, 122, 14, 124, 65, 67`)
- FCFS: 640 cylinders.
- SSTF: order 65, 67, 37, 14, 98, 122, 124, 183, total 236.
- SCAN (Right): 331. SCAN (Left): 236.
- C-SCAN (Right): 382 with the jump counted, 183 without it. C-SCAN (Left): 386.

## 3. Dry runs (narrative)

**FIFO, reference string 1, 2, 3, 1, 4, 2, three frames.** Pages 1, 2 and 3 each cause a fault and fill the three empty frames. Page 1 is requested again and is already in memory, so it is a hit. Page 4 is not in memory and all frames are full, so FIFO removes the page that arrived first, which is page 1, and frames become 4, 2, 3. Page 2 is still in memory, so it is a hit. Result: 4 faults, 2 hits, hit ratio 33.3%.

**LRU, same input.** Pages 1, 2 and 3 fault and fill the frames. Page 1 is a hit, and it now becomes the most recently used page, so page 2 is the least recently used. Page 4 faults and replaces page 2, giving frames 1, 4, 3. Page 2 is requested and is no longer in memory, so it faults; the least recently used page is now 3, so it is replaced, giving frames 1, 4, 2. Result: 5 faults, 1 hit, hit ratio 16.7%. (LRU is not always better; on short strings like this FIFO can win. On the longer default string LRU wins.)

**SCAN, head 53 moving right.** The head serves 65 (12 cylinders), 67 (2), 98 (31), 122 (24), 124 (2) and 183 (59), then continues to the disk end at 199 (16). That is 146 so far. It reverses and travels from 199 to 37 (162), then to 14 (23). Total = 146 + 162 + 23 = 331.

**C-SCAN, head 53 moving right.** The head serves the same requests up to 183 and continues to 199, a total of 146. It jumps to cylinder 0 (199 cylinders if counted), then moves right to serve 14 (14) and 37 (23). Total = 146 + 199 + 37 = 382.

## 4. Short project abstract

OS Nexus Lite is an interactive simulator that demonstrates core Operating Systems concepts through a Python and Streamlit web dashboard. It covers virtual memory, demand paging and page faults with FIFO and LRU page replacement, contiguous, linked and indexed file allocation on a simulated disk, sequential, direct and indexed file access, single-level and tree-structured directories, and the FCFS, SSTF, SCAN and C-SCAN disk scheduling algorithms with head movement calculation and graphs. Users enter their own inputs, and the tool shows step-by-step results, tables, visual disk layouts and plain-English explanations. All data is held in Python data structures, so no real files are touched and no database is needed. The project makes abstract OS theory easy to see, test and explain.

## 5. Objectives and key features

**Objectives**
1. Understand how virtual memory and demand paging let programs run with limited RAM.
2. Measure page faults, hits and hit ratio for FIFO and LRU replacement.
3. Compare contiguous, linked and indexed file allocation.
4. Compare sequential, direct and indexed file access.
5. Understand single-level and tree-structured directories.
6. Compare disk scheduling algorithms by total head movement.
7. Build a simple, working simulator in Python that is easy to explain.

**Key features**
- Single `app.py` with plain functions, no database, no login, no APIs.
- Sidebar navigation with a "How it works" box in every section.
- Frame-by-frame paging table with colored hit and fault rows, plus FIFO vs LRU comparison.
- Visual 32-block disk grid for file allocation.
- Simulated directories that can be extended by the user.
- Head movement graph, calculation line and comparison chart for disk scheduling.
- Input validation with friendly error messages, and ready-made sample inputs.

## 6. How each algorithm works

- **FIFO:** keeps pages in order of arrival. On a fault with full memory, the oldest page is removed. Hits do not change the order.
- **LRU:** on every access (hit or fault) the page becomes "most recent". On a fault with full memory, the page unused for the longest time is removed.
- **Contiguous allocation (first fit):** scans the disk for the first run of `size` free blocks side by side.
- **Linked allocation:** takes the first `size` free blocks wherever they are; each block points to the next.
- **Indexed allocation:** takes one free block as an index block and `size` free blocks for data; the index lists the data block numbers.
- **Sequential access:** reads records 1, 2, 3, ... until the target. **Direct access:** computes the position as (n − 1) × record size. **Indexed access:** looks up the block number in an index table.
- **FCFS:** serves requests in arrival order.
- **SSTF:** repeatedly serves the pending request closest to the current head position.
- **SCAN:** moves in the chosen direction serving requests, goes to the disk end, reverses and serves the rest.
- **C-SCAN:** moves in the chosen direction to the end, jumps to the opposite end, and continues in the same direction.
- **Head movement:** sum of |next position − current position| along the head path.

## 7. Viva questions and answers

1. **What is virtual memory?** A technique that lets a process use more memory than the physical RAM by keeping only needed pages in RAM and the rest on disk.
2. **What is demand paging?** Pages are loaded into memory only when they are first needed, not at program start.
3. **What is a page fault?** An access to a page that is not currently in RAM; the OS must load it from disk.
4. **What is a page table?** A table mapping each virtual page number to a physical frame number.
5. **How is a logical address split?** Into page number (address // page size) and offset (address % page size).
6. **Difference between a page and a frame?** A page is a fixed block of virtual memory; a frame is a fixed block of physical memory of the same size.
7. **How does FIFO choose a victim?** The page that has been in memory the longest.
8. **How does LRU choose a victim?** The page not used for the longest time.
9. **What is hit ratio?** Hits divided by total requests, usually shown as a percentage.
10. **What is Belady's anomaly?** For FIFO, adding more frames can sometimes increase page faults. LRU does not have this problem.
11. **What is external fragmentation?** Enough total free space exists, but not in one continuous piece. It affects contiguous allocation (see the size 7 demo).
12. **Advantages of linked allocation?** No external fragmentation and files can grow easily. Disadvantage: slow direct access and pointer overhead.
13. **Advantage of indexed allocation?** Supports direct access without fragmentation. Disadvantage: extra index block per file.
14. **Sequential vs direct access?** Sequential must read from the start; direct jumps to any record using its position.
15. **Single-level vs tree directory?** Single-level has one directory for everything and needs unique names; tree has folders inside folders and paths.
16. **What is disk seek time?** The time to move the head to the requested cylinder, which scheduling tries to reduce.
17. **Why is SSTF not always fair?** Far-away requests can starve if nearer requests keep arriving.
18. **How is SCAN different from C-SCAN?** SCAN serves requests while moving in both directions; C-SCAN serves only in one direction and jumps back, giving more uniform waiting time.
19. **Why do SCAN and C-SCAN go to the disk end?** In the classic algorithm the head travels to the last cylinder before reversing or jumping. (Variants LOOK and C-LOOK stop at the last request.)
20. **How is total head movement calculated?** Add the absolute differences between consecutive head positions, for example 53 → 98 is 45.

## 8. Troubleshooting

- **`'python' is not recognized`:** reinstall Python from python.org and tick "Add Python to PATH", or use `py -m pip install -r requirements.txt` and `py -m streamlit run app.py`.
- **`'streamlit' is not recognized`:** always start it with `python -m streamlit run app.py`.
- **`ModuleNotFoundError: No module named 'streamlit'` (or matplotlib/pandas):** run `python -m pip install -r requirements.txt` again, using the same Python that runs the app.
- **Browser does not open:** open http://localhost:8501 manually.
- **Port already in use:** run `python -m streamlit run app.py --server.port 8502`.
- **Page looks stuck or shows old data:** press R in the browser to rerun, or refresh the page. Directory changes reset when the browser tab is reloaded.
- **"File does not exist: app.py":** your Command Prompt is in the wrong folder; use `cd` to the folder containing `app.py`.
- **Input error messages:** use only whole numbers separated by commas; head and requests must lie inside the cylinder range.

## 9. Conclusion

OS Nexus Lite successfully demonstrates eight core Operating Systems topics in one simple, interactive application. The simulations produce results that match standard textbook examples: FIFO and LRU give 15 and 12 page faults on the classic reference string, and the disk scheduling algorithms give 640 (FCFS), 236 (SSTF), 331 (SCAN) and 382 (C-SCAN) cylinders of head movement. The project shows that LRU usually outperforms FIFO, that linked and indexed allocation avoid the external fragmentation which affects contiguous allocation, and that seek-optimizing algorithms greatly reduce head movement compared with FCFS. Because everything is written as short Python functions with clear comments, the project is easy to understand, run and extend.
