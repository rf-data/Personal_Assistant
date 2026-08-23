## rebuild_knowledge.py
# import

from src.model_knowledge.data_knowledge import (
                                        VisualCandidate, 
                                        DownloadedVideoSection,
                                        FrameTimestamp
                                        )


def add_frame_timestamps(
                section: DownloadedVideoSection,
                interval: float = 5.0,
                edge_offset: float = 1.0,
                ) -> DownloadedVideoSection:

    section.frame_times = []

    source_time = section.source_start + edge_offset
    end = section.source_end - edge_offset

    while source_time <= end:
        section.frame_times.append(
                    FrameTimestamp(
                         source_time=round(source_time, 3),
                         local_time=round(
                                source_time - section.download_start,
                                3,
                                )
                        )
                    )
        
        source_time += interval

    return section



def compile_download_windows(
                candidates: list[VisualCandidate],
                merge_gap: float = 2.0,
                ) -> list[tuple[float, float]]:

    if not candidates:
        return []

    windows = sorted(
                    (cand.start, cand.end)
                    for cand in candidates
                    )

    merged: list[list[float]] = []

    for start, end in windows:
        if not merged:
            merged.append([start, end])
            continue

        _, last_end = merged[-1]

        if start <= last_end + merge_gap:
                merged[-1][1] = max(last_end, end)
        else:
            merged.append([start, end])

    return [
        (start, end)
        for start, end in merged
        ]


# def compile_frame_times(
#                 candidates: list[VisualCandidate],
#                 interval: float = 5.0,
#                 ): 

#     frame_times: set[float] = set()

#     for candidate in candidates:
#         add_frame_timestamps(
#             candidate,
#             interval=interval,
#         )

#         frame_times.update(candidate.frame_times)
     
#     return sorted(frame_times)

# def assign_frame_times_to_sections(
#     frame_times: list[int | float],
#     sections: list[DownloadedVideoSection],
# ) -> dict[str, list[float]]:

#     result: dict[str, list[float]] = {
#         section.section_id: []
#         for section in sections
#     }

#     for frame_time in frame_times:
#         for section in sections:
#             if section.download_start <= frame_time <= section.download_end:
#                 local_time = frame_time - section.download_start

#                 result[section.section_id].append(
#                     round(local_time, 3)
#                 )
#                 break

#     return result


# def clean_frame_times(
#                 frame_times: list[float],
#                 min_distance: int = 2,
#                 ) -> list[int]:

#     times = sorted(set(round(t) for t in frame_times))

#     if not times:
#         return []

#     cleaned = [times[0]]

#     for t in times[1:]:
#         if t - cleaned[-1] >= min_distance:
#             cleaned.append(t)

#     return cleaned

# f_times_raw = compile_frame_times(
#     candidates=visual_candidates,
#     interval=5.0,
# )

# f_times = clean_frame_times(
#     f_times_raw,
#     min_distance=3,
# )
