from collections import OrderedDict
from django.test import TestCase
from unittest.mock import patch
from rest_framework import status
from polls.models import Poll, Choice
from polls.forms import NewPollForm
import json


class HomeGetTest(TestCase):

    def test_uses_home_template(self):
        response = self.client.get('/')
        self.assertTemplateUsed(response, 'home.html')

    def test_uses_new_poll_form(self):
        response = self.client.get('/')
        self.assertIsInstance(response.context['form'], NewPollForm)

    def test_compare_popular_polls(self):
        polls = []
        for i in range(10):
            new_poll = Poll.objects.create(text=f'Question {i}')
            for j in range(2):
                choice = Choice.objects.create(text=str(j), poll=new_poll)
                choice.votes = (12 - i) * 5  # we want i=0 to be the highest
                choice.save()
            polls.append(new_poll)
        response = self.client.get('/')
        response_popular = list(response.context['popular'])
        self.assertListEqual(response_popular, polls)


class HomePostTest(TestCase):

    def test_creates_poll(self):
        self.client.post('/', {
            'text': 'Poll Text',
            'choice_1': 'A',
            'choice_2': 'B'
        })

        new_poll = Poll.objects.first()
        self.assertEqual('Poll Text', new_poll.text)

        choices = list(Choice.objects.filter(poll=new_poll))
        self.assertEqual(len(choices), 2)
        self.assertEqual(choices[0].text, 'A')
        self.assertEqual(choices[1].text, 'B')

    def test_redirects_to_new_poll(self):
        response = self.client.post('/', {
            'text': 'Poll Text',
            'choice_1': 'A',
            'choice_2': 'B'
        })
        new_poll = Poll.objects.first()
        self.assertRedirects(response, f'/poll/{new_poll.uid}')


class ViewPollGetTest(TestCase):

    def test_uses_poll_template(self):
        poll = Poll.objects.create(text='A')
        response = self.client.get(f'/poll/{poll.uid}')
        self.assertTemplateUsed(response, 'poll.html')

    def test_displays_text_and_choices(self):
        text = 'Would you like a cookie?'
        choice_0 = 'Yes of course'
        choice_1 = 'Not really, I am full'
        poll = Poll.objects.create(text=text)
        Choice.objects.create(text=choice_0, poll=poll)
        Choice.objects.create(text=choice_1, poll=poll)
        response = self.client.get(f'/poll/{poll.uid}')
        self.assertContains(response, text)
        self.assertContains(response, choice_0)
        self.assertContains(response, choice_1)

    def test_choices_have_css_name_of_choice_id(self):
        # create another poll and some choices, so our real poll isnt the first
        random_poll = Poll.objects.create(text='Random poll')
        for _ in range(5):
            Choice.objects.create(text='random choice', poll=random_poll)

        poll = Poll.objects.create(text='Would you like a cookie?')
        choice_0 = Choice.objects.create(text='Yes of course', poll=poll)
        choice_1 = Choice.objects.create(text='Not really', poll=poll)
        response = self.client.get(f'/poll/{poll.uid}')
        self.assertContains(
            response,
            f'name="choice_id" value="{choice_0.id}"'
        )
        self.assertContains(
            response,
            f'name="choice_id" value="{choice_1.id}"'
        )

    def test_passes_in_correct_poll(self):
        Poll.objects.create(text='some other poll')
        poll = Poll.objects.create(text='my new poll')
        response = self.client.get(f'/poll/{poll.uid}')
        self.assertEqual(response.context['poll'], poll)


class PollPostTest(TestCase):

    def test_redirects_to_results_page(self):
        poll = Poll.objects.create(text='A')
        choice = Choice.objects.create(text='123', poll=poll)
        response = self.client.post(f'/poll/{poll.uid}', data={
            'choice_id': choice.id
        })
        self.assertRedirects(response, f'/poll/{poll.uid}/results')

    def test_increases_vote_by_one(self):
        poll = Poll.objects.create(text='A')
        choice = Choice.objects.create(text='123', poll=poll)
        self.client.post(f'/poll/{poll.uid}', data={
            'choice_id': choice.id
        })
        # we have to get the new choice from the database
        # the existing one we have above wont be updated
        self.assertEqual(Choice.objects.get(id=choice.id).votes, 1)

    def test_can_vote_more_than_once(self):
        poll = Poll.objects.create(text='A')
        choice = Choice.objects.create(text='123', poll=poll)
        self.client.post(f'/poll/{poll.uid}', data={
            'choice_id': choice.id
        })
        self.client.post(f'/poll/{poll.uid}', data={
            'choice_id': choice.id
        })
        self.assertEqual(Choice.objects.get(id=choice.id).votes, 2)


class ResultsTest(TestCase):

    def test_uses_results_template(self):
        poll = Poll.objects.create(text='A')
        response = self.client.get(f'/poll/{poll.uid}/results')
        self.assertTemplateUsed(response, 'results.html')

    def test_passes_in_correct_poll(self):
        Poll.objects.create(text='some other poll')
        poll = Poll.objects.create(text='The question we are asking')
        response = self.client.get(f'/poll/{poll.uid}/results')
        self.assertEqual(response.context['poll'], poll)

    def test_passes_in_a_chart(self):
        poll = Poll.objects.create(text='The question we are asking')
        response = self.client.get(f'/poll/{poll.uid}/results')
        self.assertIsNotNone(response.context['chart'])

    @patch('polls.views.Pie')
    def test_pie_chart_from_poll(self, mock_pie):
        poll = Poll.objects.create(text='The question we are asking')
        for i in range(5):
            choice = Choice.objects.create(text=str(i), poll=poll)
            choice.votes = i
            choice.save()
        self.client.get(f'/poll/{poll.uid}/results')
        mock_pie.assert_called()
        for i in range(5):
            mock_pie().add.called_with('0', 0)

    @patch('polls.views.Pie')
    def test_response_chart_matches_render(self, mock_pie):
        poll = Poll.objects.create(text='The question we are asking')
        for i in range(5):
            choice = Choice.objects.create(text=str(i), poll=poll)
            choice.votes = i
            choice.save()
        response = self.client.get(f'/poll/{poll.uid}/results')
        self.assertEqual(
            response.context['chart'],
            mock_pie().render_data_uri.return_value
        )

    def test_passes_custom_choices(self):
        poll = Poll.objects.create(text='The question we are asking')
        for i in range(5):
            Choice.objects.create(text=str(i), poll=poll)
        response = self.client.get(f'/poll/{poll.uid}/results')
        choices = response.context['poll'].choices
        self.assertIsNotNone(choices)

    def test_passes_choices_with_color(self):
        poll = Poll.objects.create(text='The question we are asking')
        for i in range(5):
            Choice.objects.create(text=str(i), poll=poll)
        response = self.client.get(f'/poll/{poll.uid}/results')
        color_choices = response.context['poll'].color_choices
        for choice in color_choices:
            self.assertIsNotNone(choice.color)

    def test_choices_ordered_by_votes(self):
        poll = Poll.objects.create(text='The question we are asking')
        for i in range(5):
            choice = Choice.objects.create(text=str(i), poll=poll)
            choice.votes = i
            choice.save()
        response = self.client.get(f'/poll/{poll.uid}/results')
        self.assertEqual(
            [x.votes for x in response.context['poll'].color_choices],
            [4, 3, 2, 1, 0]
        )

    def test_passes_in_total_votes(self):
        poll = Poll.objects.create(text='The question we are asking')
        for i in range(5):
            choice = Choice.objects.create(text=str(i), poll=poll)
            choice.votes = i
            choice.save()
        response = self.client.get(f'/poll/{poll.uid}/results')
        self.assertEqual(response.context['poll'].total_votes, 10)


class PollsListAPITest(TestCase):

    def test_can_create_poll(self):
        json_data = json.dumps({
            'text': 'My poll',
            'choices': [
                {'text': 'Choice A'},
                {'text': 'Choice B'},
            ]
        })
        response = self.client.post(
            f'/api/v1/polls',
            data=json_data,
            content_type='application/json'
        )
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

        self.assertEqual(1, Poll.objects.count())
        poll = Poll.objects.first()
        self.assertEqual('My poll', poll.text)

        self.assertEqual(2, Choice.objects.count())
        choice = Choice.objects.first()
        self.assertEqual('Choice A', choice.text)
        self.assertEqual(poll, choice.poll)

    def test_invalid_data_raises_400(self):
        response = self.client.post(f'/api/v1/polls', data={
            'text': 'My poll',
        })
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

    def test_can_get_existing_polls(self):
        poll_0 = Poll.objects.create(text='My first poll')
        choice_0 = Choice.objects.create(text='First', poll=poll_0, votes=2)
        choice_1 = Choice.objects.create(text='Second', poll=poll_0, votes=5)

        poll_1 = Poll.objects.create(text='My second poll')
        choice_2 = Choice.objects.create(text='Third', poll=poll_1, votes=21)
        choice_3 = Choice.objects.create(text='Fourth', poll=poll_1, votes=8)

        response = self.client.get(f'/api/v1/polls')
        self.assertEqual(response.data, [
            OrderedDict(
                id=poll_0.id,
                uid=poll_0.uid,
                text=poll_0.text,
                pub_date=poll_0.pub_date.astimezone().isoformat(),
                choices=[
                    OrderedDict(
                        id=choice_0.id,
                        text=choice_0.text,
                        votes=choice_0.votes,
                    ),
                    OrderedDict(
                        id=choice_1.id,
                        text=choice_1.text,
                        votes=choice_1.votes
                    )
                ]
            ),
            OrderedDict(
                id=poll_1.id,
                uid=poll_1.uid,
                text=poll_1.text,
                pub_date=poll_1.pub_date.astimezone().isoformat(),
                choices=[
                    OrderedDict(
                        id=choice_2.id,
                        text=choice_2.text,
                        votes=choice_2.votes,
                    ),
                    OrderedDict(
                        id=choice_3.id,
                        text=choice_3.text,
                        votes=choice_3.votes
                    )
                ]
            )
        ])


class PollDetailAPITest(TestCase):

    def test_can_get_poll_data(self):
        poll = Poll.objects.create(text='My poll text')
        choice_0 = Choice.objects.create(text='First', poll=poll, votes=5)
        choice_1 = Choice.objects.create(text='Second', poll=poll, votes=13)
        response = self.client.get(f'/api/v1/poll/{poll.uid}')
        self.assertDictEqual(response.data, {
            'id': poll.id,
            'text': poll.text,
            'pub_date': poll.pub_date.astimezone().isoformat(),
            'uid': poll.uid,
            'choices': [
                OrderedDict(
                    id=choice_0.id,
                    text=choice_0.text,
                    votes=choice_0.votes,
                ),
                OrderedDict(
                    id=choice_1.id,
                    text=choice_1.text,
                    votes=choice_1.votes
                )
            ]
        })
