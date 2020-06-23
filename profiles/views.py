import json
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.contrib.auth.models import User
from drf_yasg.utils import swagger_auto_schema
from urllib.request import urlopen
from utils.swagger import set_example
from profiles.models import Leaderboard


@swagger_auto_schema(
        operation_id='update pull requests status',
        method='post',
        responses={
            '200': set_example({'detail':'Successfully updated leaderboard'}),
            '400': set_example({"detail":"Sorry, there is some issue with the webhooks."}),
            '404': set_example({"detail":"Cannot retrieve the user."})
        },
)
@api_view(['post'])
def pull_request(request):
    """
    This API is to keep a track of the PR's opened and the \
    contribution by any user by any user. This is automatically \
    handled by webhooks in the git repos.
    """
    print(request.data)
    try:
        action = request.data['action']
        username = request.data['sender']['login']
        merged = request.data['pull_request']['merged']
    except:
        return Response(
            {"detail":"Sorry, there is some issue with the webhooks."},
            status=status.HTTP_400_BAD_REQUEST
        )
    else:
        try:
            user = User.objects.get(username=username)
            leaderboard = Leaderboard.objects.get(username=user)
        except:
            return Response(
                {"detail":"Cannot retrieve the user."},
                status=status.HTTP_404_NOT_FOUND
            )
        else:
            if action == 'opened':
                leaderboard.pr_opened += 1
                leaderboard.save()
            elif action == 'closed' and merged:
                leaderboard.pr_merged += 1
                issue_response = urlopen(request.data['pull_request']['_links']['issue']['href'])
                string = issue_response.read().decode('utf-8')
                issue_response_json_obj = json.loads(string)
                print(issue_response_json_obj)
                for label in issue_response_json_obj['labels']:
                    if label == 'good first issue':
                        leaderboard.good_first_issue = True
                        if leaderboard.medium_issues_solved >= 2:
                            leaderboard.milestone_achieved = True
                    elif label == 'medium':
                        leaderboard.medium_issues_solved += 1
                        if(leaderboard.good_first_issue and leaderboard.medium_issues_solved == 2):
                            leaderboard.milestone_achieved = True
                    elif label == 'hard':
                        leaderboard.hard_issues_solved += 1

                leaderboard.save()
            else:
                pass
            return Response(
                {'detail':'Successfully updated leaderboard'},
                status=status.HTTP_200_OK
            )

@api_view(['post'])
def issue(request):
    print(request.data)
    return Response(
                request.data,
                status=status.HTTP_200_OK
            )