#!/usr/bin/env python

# https://pypi.org/project/simple-term-menu/
from simple_term_menu import TerminalMenu
import subprocess
import argparse
import json
import os
import stat


def parse_args():
    parser = argparse.ArgumentParser(description='AWS ECS Exec Helper Utility')
    parser.add_argument('--profile', help="The AWS profile name to assume, that shortcuts the selection menu")
    parser.add_argument('--region', help="The AWS region to use, that shortcuts the selection menu")
    parser.add_argument('--cluster_arn', help="The ECS cluster ARN")
    return parser.parse_args()


def get_choice_from_menu(options: list[str], title: str) -> str:
    if len(options) == 1:
        # Don't ask redundant questions
        return options[0]

    terminal_menu = TerminalMenu(
        options,
        title=title,
        skip_empty_entries=True,
        show_shortcut_hints=False,
        show_shortcut_hints_in_status_bar=False)
    menu_entry_index = terminal_menu.show()
    return options[menu_entry_index]


def list_profiles() -> list[str]:
    all_profiles = subprocess.check_output(["aws", "configure", "list-profiles"], text=True).split("\n")
    all_profiles.sort()
    return [profile for profile in all_profiles if profile]


def list_regions() -> list[str]:
    # TODO: be better
    return ["us-west-2", "us-east-1", "eu-central-1", "ap-southeast-2"]


def list_ecs_clusters(profile: str, region: str) -> list[str]:
    clusters_json = json.loads(subprocess.check_output(["aws", "--profile", profile, "--region", region, "ecs", "list-clusters"], text=True))
    return clusters_json['clusterArns']


def list_services(profile: str, region: str, cluster_arn: str) -> list[str]:
    services_json = json.loads(subprocess.check_output(
        ["aws", "--profile", profile, "--region", region, "ecs", "list-services", "--cluster", cluster_arn],
        text=True))
    return services_json['serviceArns']


def list_tasks(profile: str, region: str, cluster_arn: str, service_arn: str) -> list[str]:
    tasks_json = json.loads(subprocess.check_output(
        ["aws", "--profile", profile, "--region", region, "ecs", "list-tasks", "--cluster", cluster_arn, "--service-name", service_arn],
        text=True))
    return tasks_json['taskArns']


def list_containers(profile: str, region: str, cluster_arn: str, task_arn: str) -> list[str]:
    tasks_json = json.loads(subprocess.check_output(
        ["aws", "--profile", profile, "--region", region, "ecs", "describe-tasks", "--cluster", cluster_arn, "--tasks", task_arn],
        text=True))
    containers = tasks_json['tasks'][0]['containers']
    return [container['name'] for container in containers]


def main():
    args = parse_args()
    if not args.profile:
        args.profile = get_choice_from_menu(list_profiles(), "Choose an AWS CLI profile")
    if not args.region:
        args.region = get_choice_from_menu(list_regions(), "Choose a region")
    if not args.cluster_arn:
        args.cluster_arn = get_choice_from_menu(list_ecs_clusters(args.profile, args.region), "Choose a cluster")
    service_arn = get_choice_from_menu(list_services(args.profile, args.region, args.cluster_arn), "Choose a service")
    task_arn = get_choice_from_menu(list_tasks(args.profile, args.region, args.cluster_arn, service_arn), "Choose a task")
    container_name = get_choice_from_menu(list_containers(args.profile, args.region, args.cluster_arn, task_arn), "Choose a container")

    # This is a pretty ugly workaround to be able to use bash to run the AWS cli command.  Can't quite get the exec to
    # work correctly any other way.
    filename = "temp-ecs-exec.sh"
    with open(filename, "w") as f:
        f.write("#!/bin/bash\n")
        f.write(" ".join(["aws", "--profile", args.profile, "--region", args.region,
                          "ecs", "execute-command",
                          "--cluster", args.cluster_arn,
                          "--task", task_arn,
                          "--container", container_name,
                          "--command", "'/bin/bash'",
                          "--interactive"]))
    st = os.stat(filename)
    os.chmod(filename, st.st_mode | stat.S_IEXEC)
    subprocess.call([f"./{filename}"], shell=True)

    # TODO: can't quite get this to work
    # subprocess.call(["aws", "--profile", args.profile, "--region", args.region,
    #                  "ecs", "execute-command",
    #                  "--cluster", args.cluster_arn,
    #                  "--task", task_arn,
    #                  "--container", container_name,
    #                  "--command", "/bin/bash",
    #                  "--interactive"], shell=True)


if __name__ == "__main__":
    main()
