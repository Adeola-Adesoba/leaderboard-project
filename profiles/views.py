from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.contrib.auth.models import User
from drf_yasg.utils import swagger_auto_schema
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
                leaderboard.save()
            else:
                pass
            return Response(
                {'detail':'Successfully updated leaderboard'},
                status=status.HTTP_200_OK
            )

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
def issue(request):
    """
    This API is to keep a track of the issues closed and the \
    contribution the user assigned to close it. This is \
    automatically handled by webhooks in the git repository \
    or repositories being tracked.
    """

    try:
        action = request.data["action"] #Receives action done upon the issue
        labels = request.data["issue"]["labels"] #Receives a list of labels of the issue
        username = request.data["issue"]["assignee"]["login"] #Receives username of assigned user
    except:
        return Response(
            {"detail":"Sorry, there is some issue with the webhooks."},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        #Getting leaderboard object of the user
        user = User.objects.get(username=username)
        leaderboard = Leaderboard.objects.get(username=user)
    except:
        return Response(
            {"detail":"Cannot retrieve the user."},
            status=status.HTTP_404_NOT_FOUND
        )

    if action == 'closed': #if the issue has been closed.
        '''Take note that we assume issue to be closed only when a PR
        has fixed it. If not, make sure that nobody is assigned so that
        no wrong person gets points.'''
        for label in labels: 
            '''looking for desired labels from the list of labels to change
            the leaderboard fields as done below'''
            if label["name"] == 'good first issue':
                leaderboard.good_first_issue = True
                if leaderboard.medium_issues_solved >= 2: #Milestone check
                    leaderboard.milestone_achieved = True
                leaderboard.save()
            elif label["name"] == 'medium':
                leaderboard.medium_issues_solved += 1
                #Milestone check
                if(leaderboard.good_first_issue and leaderboard.medium_issues_solved == 2):
                    leaderboard.milestone_achieved = True
                leaderboard.save()
            elif label["name"] == 'hard':
                leaderboard.hard_issues_solved += 1
                leaderboard.save()
            else:
                pass  #Search in rest labels

    return Response(
                {'detail':'Successfully updated leaderboard'},
                status=status.HTTP_200_OK
        )
