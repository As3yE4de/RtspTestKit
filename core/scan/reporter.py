from collections import defaultdict
from utils import tui as u

def _sort_results(results: list[tuple], targets: list[str]) -> list[tuple]:
    """
    Sort results.

    Args:
        results: A list of tuple (get from start_scan())
        targets: A list of targets

    Returns:
        A sorted list of tuples.
    """
    target_order = {target: index for index, target in enumerate(targets)}

    def sort_key(item):
        host, port, state, service = item
        host_idx = target_order.get(host, 9999)
        return (host_idx, port)

    return sorted(results, key=sort_key)


def report_scan_results(results: list[tuple], targets: list[str], output_file: str | None = None) -> None:
    """
    Print results to console and save the results to TSV file (optionally).

    Args:
        results: A sorted list of tuple
        targets: A list of targets
        output_file: Path for the output
    """
    if not results:
        print(f"{u.Retro.WARNING}No open port found on the target.{u.Retro.RESET}")
        return

    sorted_results = _sort_results(results, targets)

    grouped_results = defaultdict(list)
    for item in sorted_results:
        grouped_results[item[0]].append(item)

    print(f"\n{u.Retro.SUCCESS}Scan results: (Found {len(sorted_results)} open port(s)):{u.Retro.RESET}")

    lines_to_save = []

    for i, target in enumerate(targets):
        is_last_target = (i == len(targets) - 1)
        target_prefix = "└── " if is_last_target else "├── "

        print(f"{target_prefix}{u.Retro.NEON_GREEN}{target}{u.Retro.RESET}")

        indent = "    " if is_last_target else "│   "
        target_ports = grouped_results[target]

        for j, (host, port, state, service) in enumerate(target_ports):
            is_last_port = (j == len(target_ports) - 1)
            port_prefix = "└── " if is_last_port else "├── "
            svc_color = u.Retro.NEON_GREEN if service == "RTSP" or service == "RTSPS" else u.Retro.NEON_YELLOW
            print(f"{indent}{port_prefix}{port:<6} {svc_color}[{service}]{u.Retro.RESET} - {state}")
            lines_to_save.append(f"{host}\t{port}\t{state}\t{service}")

    print()

    if output_file:
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write("Host\tPort\tState\tService\n")
                for line in lines_to_save:
                    f.write(line + "\n")
            print(f"{u.Retro.SUCCESS}Saved results to file: {output_file}{u.Retro.RESET}\n")
        except Exception as e:
            print(f"{u.Retro.FAILED}Error occurs while saving file: {e}{u.Retro.RESET}\n")
