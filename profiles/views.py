from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.contrib.auth.models import User
from drf_yasg.utils import swagger_auto_schema
from decouple import config
from utils.swagger import set_example
from profiles.models import Leaderboard
from profiles.responses import leaderboard_response_example_200



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
    try:
        # Getting relevant information from webhook.
        action = request.data['action'] # Recieves action done on pull request
        username = request.data['sender']['login'] # Recieves the contributor.
        merged = request.data['pull_request']['merged'] # Recieves the boolean merged.

    except:
        return Response(
            {"detail":"Sorry, there is some issue with the webhooks."},
            status=status.HTTP_400_BAD_REQUEST
        )
    else:
        try:
            # Fetching the leaderboard object of the contributor.
            user = User.objects.get(username=username)
            leaderboard = Leaderboard.objects.get(username=user)

        except:
            return Response(
                {"detail":"Cannot retrieve the user."},
                status=status.HTTP_404_NOT_FOUND
            )
        else:
            # Keeping count by the action taken on pull request.

            if action == 'opened':
                leaderboard.pr_opened += 1
                leaderboard.save()
            elif action == 'closed' and merged:
                leaderboard.pr_merged += 1
                leaderboard.save()
            else:
                pass

            return Response(
                {'detail':'Successfully updated leaderboard'},
                status=status.HTTP_200_OK
            )

@swagger_auto_schema(
        operation_id='update issue and milestone status',
        method='post',
        responses={
            '200': set_example({'detail':'Successfully updated leaderboard'}),
            '400': set_example({"detail":"Sorry, there is some issue with the webhooks."}),
            '404': set_example({"detail":"Cannot retrieve the user."})
        },
)
@api_view(['post'])
def issue(request):
    """
    This API is to keep a track of the issues closed and the \
    contribution of the user assigned to close it. This is \
    automatically handled by webhooks in the git repository \
    or repositories being tracked.
    """

    # Getting the points from the .env
    gfi_points = int(config('GOOD_FIRST_ISSUE_POINTS'))
    medium_issue_points = int(config('MEDIUM_ISSUE_POINTS'))
    hard_issue_points = int(config('HARD_ISSUE_POINTS'))

    try:
        action = request.data["action"] #Receives action done upon the issue
        labels = request.data["issue"]["labels"] #Receives a list of labels of the issue
        assignee = request.data["issue"]["assignee"] #Receives username of assigned user
    except:
        return Response(
            {"detail":"Sorry, there is some issue with the webhooks."},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        # Getting leaderboard object of the contributor.
        user = User.objects.get(username=assignee['login'])
        leaderboard = Leaderboard.objects.get(username=user)

    except:
        return Response(
            {"detail":"Cannot retrieve the user."},
            status=status.HTTP_404_NOT_FOUND
        )

    if action == 'closed': #if the issue has been closed.
        '''
        Take note that we assume issue to be closed, only when a PR
        has fixed it. If the issue is not fixed and needs to be closed,
        make sure that nobody is assigned the issue, so that no user gets
        the points.
        '''
        for label in labels:
            '''
            looking for desired labels from the list of labels to change
            the leaderboard fields as done below
            '''
            if label["name"] == 'good first issue':
                leaderboard.good_first_issue = True
                leaderboard.points += gfi_points #Update points
                if leaderboard.medium_issues_solved >= 2: #Milestone check
                    leaderboard.milestone_achieved = True
                leaderboard.save() #Save changes

            elif label["name"] == 'medium':
                leaderboard.medium_issues_solved += 1
                leaderboard.points += medium_issue_points #Update points

                #Milestone check
                if(
                    leaderboard.good_first_issue and
                    leaderboard.medium_issues_solved >= 2
                ):
                    leaderboard.milestone_achieved = True

                leaderboard.save() #Save changes

            elif label["name"] == 'hard':
                leaderboard.hard_issues_solved += 1
                leaderboard.points += hard_issue_points #Update points
                leaderboard.save() #Save changes
            else:
                pass  #Search in rest labels

    return Response(
                {'detail':'Successfully updated leaderboard'},
                status=status.HTTP_200_OK
        )

@swagger_auto_schema(
        operation_id='get leaderboard',
        method='get',
        responses={
            '200': set_example(leaderboard_response_example_200),
        },
)
@api_view(['get'])
def list_leaderboard(request):
    '''This view lists all contributors along with their \
    respective details in descending order along with ranks'''

    leaderboard_obj = Leaderboard.objects.order_by('-points')
    response_obj = []
    ctr = 1
    for obj in leaderboard_obj:
        details = {
            'rank' : ctr,
            'username' : obj.username.username,
            'points' : obj.points,
            'pr_opened' : obj.pr_opened,
            'pr_merged' : obj.pr_merged,
            'good_first_issue' : obj.good_first_issue,
            'milestone_achieved' : obj.milestone_achieved,
            'medium_issues_solved' : obj.medium_issues_solved,
            'hard_issues_solved' : obj.hard_issues_solved
        }
        ctr = ctr + 1
        response_obj.append(details)

    return Response(
                response_obj,
                status=status.HTTP_200_OK
    )
