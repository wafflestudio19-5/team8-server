from rest_framework import status
from django.test import TestCase
from factory.django import DjangoModelFactory

from user.models import User
from user.serializers import jwt_token_of
from user.tests import UserFactory
from location.tests import LocationFactory
from article.models import Article, Comment


class ArticleFactory(DjangoModelFactory):
    class Meta:
        model = Article


class CommentFactory(DjangoModelFactory):
    class Meta:
        model = Comment


class PostArticleTestCase(TestCase):
    @classmethod
    def setUp(cls):

        cls.user1 = UserFactory(
            phone_number="01011112222",
            email="wafflemarket@test.com",
            username="steve",
        )
        cls.user1_token = "JWT " + jwt_token_of(User.objects.get(phone_number="01011112222"))

        cls.location1 = LocationFactory(
            code="1111011700",
            place_name="서울특별시 종로구 당주동",
        )
        cls.user1.location = cls.location1
        cls.user1.save()

        cls.post_data = {
            "price": 3040000,
            "title": "맥북 판매",
            "content": "성능 좋은 맥북 판매해요.",
            "category": "디지털기기",
        }

    def test_post_article_no_login(self):
        # no token
        data = self.post_data.copy()
        response = self.client.post("/api/v1/article/", data=data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        article_count = Article.objects.count()
        self.assertEqual(article_count, 0)

    def test_post_article_wrong_information(self):
        # no price title, content, category
        data = self.post_data.copy()
        data.pop("price")
        data.pop("title")
        data.pop("content")
        data.pop("category")
        response = self.client.post("/api/v1/article/", data=data, HTTP_AUTHORIZATION=self.user1_token)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        res_data = response.json()
        self.assertEqual(res_data["title"], ["This field is required."])
        self.assertEqual(res_data["content"], ["This field is required."])
        self.assertEqual(res_data["category"], ["This field is required."])

        article_count = Article.objects.count()
        self.assertEqual(article_count, 0)

        # invalid price
        data = self.post_data.copy()
        data["price"] = -3000
        response = self.client.post("/api/v1/article/", data=data, HTTP_AUTHORIZATION=self.user1_token)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        res_data = response.json()
        self.assertEqual(res_data["non_field_errors"], ["가격은 0 이상의 정수로 입력되어야 해요."])

        article_count = Article.objects.count()
        self.assertEqual(article_count, 0)

        # invalid title, content
        data = self.post_data.copy()
        data["title"] = "  "
        data["content"] = "  "
        response = self.client.post("/api/v1/article/", data=data, HTTP_AUTHORIZATION=self.user1_token)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        res_data = response.json()
        self.assertEqual(res_data["title"], ["This field may not be blank."])
        self.assertEqual(res_data["content"], ["This field may not be blank."])

        article_count = Article.objects.count()
        self.assertEqual(article_count, 0)

        # invalid category
        data = self.post_data.copy()
        data["category"] = "notvalidcategory"
        response = self.client.post("/api/v1/article/", data=data, HTTP_AUTHORIZATION=self.user1_token)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        res_data = response.json()
        self.assertEqual(res_data["non_field_errors"], ["카테고리가 부적절해요."])

        article_count = Article.objects.count()
        self.assertEqual(article_count, 0)

    def test_post_article_sucess(self):
        # successively add new article
        data = self.post_data.copy()
        response = self.client.post("/api/v1/article/", data=data, HTTP_AUTHORIZATION=self.user1_token)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        article = Article.objects.filter(seller=self.user1)
        self.assertEqual(article.count(), 1)
        article = article[0]
        self.assertIsNone(article.buyer)
        self.assertIsNotNone(article.location)
        self.assertIsNotNone(article.title)
        self.assertIsNotNone(article.content)
        self.assertIsNotNone(article.category)
        self.assertEqual(article.price, 3040000)
        self.assertIsNotNone(article.created_at)
        self.assertIsNone(article.sold_at)
        self.assertIsNone(article.buyer)


class PutArticleTestCase(TestCase):
    @classmethod
    def setUp(cls):

        cls.user1 = UserFactory(phone_number="01011112222", username="steve")
        cls.user1_token = "JWT " + jwt_token_of(User.objects.get(phone_number="01011112222"))
        cls.user2 = UserFactory(phone_number="01022223333", username="mark")
        cls.user2_token = "JWT " + jwt_token_of(User.objects.get(phone_number="01022223333"))

        cls.location1 = LocationFactory(code="1111011700", place_name="서울특별시 종로구 당주동")
        cls.user1.location = cls.location1
        cls.user1.save()

        cls.article1 = ArticleFactory(
            seller=cls.user1,
            location=cls.location1,
            price=3040000,
            title="맥북 판매",
            content="성능 좋은 맥북 판매해요.",
            category="디지털기기",
        )

        cls.put_data = {
            "price": 2040000,
            "title": "삼성 노트북 판매",
            "content": "성능 좋은 삼성 노트북 판매해요.",
            "category": "생활가전",
        }

    def check_article_not_changed(self, article_id):
        article = Article.objects.get(id=article_id)
        self.assertEqual(article.price, 3040000)
        self.assertEqual(article.title, "맥북 판매")
        self.assertEqual(article.content, "성능 좋은 맥북 판매해요.")
        self.assertEqual(article.category, "디지털기기")

    def test_put_article_no_login(self):
        pk = str(self.article1.id) + "/"
        # no token
        data = self.put_data.copy()
        response = self.client.put("/api/v1/article/" + pk, data=data, content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        self.check_article_not_changed(self.article1.id)

    def test_put_article_not_seller(self):
        pk = str(self.article1.id) + "/"
        # invalid token
        data = self.put_data.copy()
        response = self.client.put(
            "/api/v1/article/" + pk, data=data, content_type="application/json", HTTP_AUTHORIZATION=self.user2_token
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        res_data = response.json()
        self.assertEqual(res_data[0], "작성자 외에는 게시글을 수정할 수 없습니다.")

        self.check_article_not_changed(self.article1.id)

    def test_put_article_wrong_id(self):
        # wrong pk
        wrong_pk = str(self.article1.id + 3) + "/"
        data = self.put_data.copy()
        response = self.client.put(
            "/api/v1/article/" + wrong_pk,
            data=data,
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user1_token,
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        res_data = response.json()
        self.assertEqual(res_data[0], "해당하는 게시글을 찾을 수 없습니다.")

        self.check_article_not_changed(self.article1.id)

    def test_put_article_wrong_information(self):
        pk = str(self.article1.id) + "/"
        # invalid title, content
        data = self.put_data.copy()
        data["title"] = " "
        data["content"] = " "
        response = self.client.put(
            "/api/v1/article/" + pk, data=data, content_type="application/json", HTTP_AUTHORIZATION=self.user1_token
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        res_data = response.json()
        self.assertEqual(res_data["title"], ["This field may not be blank."])
        self.assertEqual(res_data["content"], ["This field may not be blank."])

        self.check_article_not_changed(self.article1.id)

        # invalid price
        data = self.put_data.copy()
        data["price"] = "invalid"
        response = self.client.put(
            "/api/v1/article/" + pk, data=data, content_type="application/json", HTTP_AUTHORIZATION=self.user1_token
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        res_data = response.json()
        self.assertEqual(res_data["price"], ["A valid integer is required."])

        self.check_article_not_changed(self.article1.id)

        # invalid category
        data = self.put_data.copy()
        data["category"] = "invalid"
        response = self.client.put(
            "/api/v1/article/" + pk, data=data, content_type="application/json", HTTP_AUTHORIZATION=self.user1_token
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        res_data = response.json()
        self.assertEqual(res_data["non_field_errors"], ["카테고리가 부적절해요."])

        self.check_article_not_changed(self.article1.id)

    def test_put_article_partial_info_success(self):
        pk = str(self.article1.id) + "/"
        # sucessively change article information partially
        data = self.put_data.copy()
        data.pop("title")
        data.pop("category")
        response = self.client.put(
            "/api/v1/article/" + pk, data=data, content_type="application/json", HTTP_AUTHORIZATION=self.user1_token
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        article = Article.objects.get(id=self.article1.id)
        self.assertEqual(article.price, 2040000)
        self.assertEqual(article.title, "맥북 판매")
        self.assertEqual(article.content, "성능 좋은 삼성 노트북 판매해요.")
        self.assertEqual(article.category, "디지털기기")

    def test_put_article_success(self):
        pk = str(self.article1.id) + "/"
        # sucessively change article information
        data = self.put_data.copy()
        response = self.client.put(
            "/api/v1/article/" + pk, data=data, content_type="application/json", HTTP_AUTHORIZATION=self.user1_token
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        article = Article.objects.get(id=self.article1.id)
        self.assertEqual(article.price, 2040000)
        self.assertEqual(article.title, "삼성 노트북 판매")
        self.assertEqual(article.content, "성능 좋은 삼성 노트북 판매해요.")
        self.assertEqual(article.category, "생활가전")


class DeleteArticleTestCase(TestCase):
    @classmethod
    def setUp(cls):
        cls.user1 = UserFactory(phone_number="01011112222", username="steve")
        cls.user1_token = "JWT " + jwt_token_of(User.objects.get(phone_number="01011112222"))
        cls.user2 = UserFactory(phone_number="01022223333", username="mark")
        cls.user2_token = "JWT " + jwt_token_of(User.objects.get(phone_number="01022223333"))

        cls.location1 = LocationFactory(code="1111011700", place_name="서울특별시 종로구 당주동")
        cls.user1.location = cls.location1
        cls.user1.save()

        cls.article1 = ArticleFactory(
            seller=cls.user1,
            location=cls.location1,
            price=3040000,
            title="맥북 판매",
            content="성능 좋은 맥북 판매해요.",
            category="디지털기기",
        )

    def check_article_not_deleted(self, article_id):
        article = Article.objects.filter(id=article_id)
        self.assertEqual(article.count(), 1)
        article = article[0]

    def test_delete_article_no_login(self):
        pk = str(self.article1.id) + "/"
        # no token
        response = self.client.delete("/api/v1/article/" + pk)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        self.check_article_not_deleted(self.article1.id)

    def test_delete_article_not_seller(self):
        pk = str(self.article1.id) + "/"
        # invalid token
        response = self.client.delete("/api/v1/article/" + pk, HTTP_AUTHORIZATION=self.user2_token)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        res_data = response.json()
        self.assertEqual(res_data[0], "작성자 외에는 게시글을 삭제할 수 없습니다.")

        self.check_article_not_deleted(self.article1.id)

    def test_delete_article_wrong_id(self):
        # wrong pk
        wrong_pk = str(self.article1.id + 3) + "/"
        response = self.client.delete("/api/v1/article/" + wrong_pk, HTTP_AUTHORIZATION=self.user1_token)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        res_data = response.json()
        self.assertEqual(res_data[0], "해당하는 게시글을 찾을 수 없습니다.")

        self.check_article_not_deleted(self.article1.id)

    def test_delete_article_success(self):
        article_id = self.article1.id
        pk = str(self.article1.id) + "/"
        # sucessively delete article
        response = self.client.delete("/api/v1/article/" + pk, HTTP_AUTHORIZATION=self.user1_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        article = Article.objects.filter(id=article_id)
        self.assertEqual(article.count(), 0)


class PostCommentTestCase(TestCase):
    @classmethod
    def setUp(cls):
        cls.user1 = UserFactory(
            phone_number="01011112222",
            username="steve",
        )
        cls.user1_token = "JWT " + jwt_token_of(User.objects.get(phone_number="01011112222"))
        cls.user2 = UserFactory(
            phone_number="01022223333",
            username="mark",
        )
        cls.user2_token = "JWT " + jwt_token_of(User.objects.get(phone_number="01022223333"))

        cls.location1 = LocationFactory(
            code="1111011700",
            place_name="서울특별시 종로구 당주동",
        )
        cls.user1.location = cls.location1
        cls.user1.save()

        cls.article = ArticleFactory(
            seller=cls.user1,
            location=cls.location1,
            price=3040000,
            title="맥북 판매",
            content="성능 좋은 맥북 판매해요.",
            category="디지털기기",
        )
        cls.post_data = {
            "content": "맥북 구매 원합니다.",
        }

    def test_post_comment_no_login(self):
        pk = str(self.article.id)
        # no token
        data = self.post_data.copy()
        response = self.client.post("/api/v1/article/%s/comment/" % pk, data=data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        self.assertEqual(Comment.objects.count(), 0)

    def test_post_comment_wrong_information(self):
        pk = str(self.article.id)
        # no content
        response = self.client.post("/api/v1/article/%s/comment/" % pk, data={}, HTTP_AUTHORIZATION=self.user2_token)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(Comment.objects.count(), 0)

        # invalid content
        response = self.client.post(
            "/api/v1/article/%s/comment/" % pk, data={"content": "  "}, HTTP_AUTHORIZATION=self.user2_token
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(Comment.objects.count(), 0)

    def test_post_comment_sucess(self):
        pk = str(self.article.id)
        # successively add new comment
        data = self.post_data.copy()
        response = self.client.post("/api/v1/article/%s/comment/" % pk, data=data, HTTP_AUTHORIZATION=self.user2_token)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        res_data = response.data
        self.assertEqual(len(res_data["comments"]), 1)
        comment = res_data["comments"][0]
        self.assertEqual(comment["id"], 1)
        self.assertEqual(comment["commenter"]["id"], self.user2.id)
        self.assertEqual(comment["content"], "맥북 구매 원합니다.")
        self.assertIsNotNone(comment["created_at"])
        self.assertIsNone(comment["deleted_at"])
        self.assertEqual(comment["replies"], [])

        article = Article.objects.get(seller=self.user1)
        comments = Comment.objects.filter(commenter=self.user2)
        self.assertEqual(comments.count(), 1)
        comment = comments[0]
        self.assertIsNotNone(comment.commenter)
        self.assertEqual(comment.article, article)
        self.assertEqual(comment.content, "맥북 구매 원합니다.")
        self.assertIsNone(comment.parent)
        self.assertIsNotNone(comment.created_at)
        self.assertIsNone(comment.deleted_at)


class DeleteCommentTestCase(TestCase):
    @classmethod
    def setUp(cls):
        cls.user1 = UserFactory(
            phone_number="01011112222",
            username="steve",
        )
        cls.user1_token = "JWT " + jwt_token_of(User.objects.get(phone_number="01011112222"))
        cls.user2 = UserFactory(
            phone_number="01022223333",
            username="mark",
        )
        cls.user2_token = "JWT " + jwt_token_of(User.objects.get(phone_number="01022223333"))

        cls.location1 = LocationFactory(
            code="1111011700",
            place_name="서울특별시 종로구 당주동",
        )
        cls.user1.location = cls.location1
        cls.user1.save()

        cls.article = ArticleFactory(
            seller=cls.user1,
            location=cls.location1,
            price=3040000,
            title="맥북 판매",
            content="성능 좋은 맥북 판매해요.",
            category="디지털기기",
        )
        cls.comment1 = CommentFactory(
            commenter=cls.user2,
            article=cls.article,
            content="맥북 구매 원합니다.",
            parent=None,
        )
        cls.comment2 = CommentFactory(
            commenter=cls.user1,
            article=cls.article,
            content="직거래 가능하신가요?",
            parent=cls.comment1,
        )

    def check_comment_not_deleted(self, comment_id):
        comment = Comment.objects.filter(id=comment_id)
        self.assertEqual(comment.count(), 1)
        comment = comment[0]
        self.assertIsNone(comment.deleted_at)

    def test_delete_comment_no_login(self):
        a_id = str(self.article.id)
        c_id = str(self.comment1.id)
        # no token
        response = self.client.delete("/api/v1/article/%s/comment/%s/" % (a_id, c_id), data={})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        self.assertEqual(Comment.objects.count(), 2)
        self.check_comment_not_deleted(self.comment1.id)

    def test_delete_comment_not_commenter(self):
        a_id = str(self.article.id)
        c_id = str(self.comment1.id)
        # wrong commenter
        response = self.client.delete(
            "/api/v1/article/%s/comment/%s/" % (a_id, c_id), data={}, HTTP_AUTHORIZATION=self.user1_token
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        res_data = response.json()
        self.assertEqual(res_data[0], "작성자 외에는 댓글을 삭제할 수 없습니다.")

        self.assertEqual(Comment.objects.count(), 2)
        self.check_comment_not_deleted(self.comment1.id)

    def test_delete_comment_wrong_article_id(self):
        # wrong article id
        a_id = str(self.article.id + 10)
        c_id = str(self.comment1.id)

        response = self.client.delete(
            "/api/v1/article/%s/comment/%s/" % (a_id, c_id), data={}, HTTP_AUTHORIZATION=self.user2_token
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        res_data = response.json()
        self.assertEqual(res_data[0], "해당하는 게시글을 찾을 수 없습니다.")

        self.assertEqual(Comment.objects.count(), 2)
        self.check_comment_not_deleted(self.comment1.id)

    def test_delete_comment_wrong_comment_id(self):
        a_id = str(self.article.id)
        # wrong comment id
        c_id = str(self.comment1.id + 10)

        response = self.client.delete(
            "/api/v1/article/%s/comment/%s/" % (a_id, c_id), data={}, HTTP_AUTHORIZATION=self.user2_token
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        res_data = response.json()
        self.assertEqual(res_data[0], "해당하는 댓글을 찾을 수 없습니다.")

        self.assertEqual(Comment.objects.count(), 2)
        self.check_comment_not_deleted(self.comment1.id)

    def test_delete_comment_success(self):
        a_id = str(self.article.id)
        c_id = str(self.comment1.id)
        # sucessively delete comment
        response = self.client.delete(
            "/api/v1/article/%s/comment/%s/" % (a_id, c_id), data={}, HTTP_AUTHORIZATION=self.user2_token
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        comment = Comment.objects.filter(id=self.comment1.id)
        self.assertEqual(comment.count(), 1)
        self.assertEqual(Comment.objects.count(), 2)
        self.assertIsNotNone(comment[0].deleted_at)

        self.check_comment_not_deleted(self.comment2.id)

        reply = Comment.objects.get(id=self.comment2.id)
        self.assertIsNotNone(reply.parent.deleted_at)

        c_id = str(self.comment2.id)
        # sucessively delete reply
        response = self.client.delete(
            "/api/v1/article/%s/comment/%s/" % (a_id, c_id), data={}, HTTP_AUTHORIZATION=self.user1_token
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        comment = Comment.objects.filter(id=self.comment2.id)
        self.assertEqual(comment.count(), 1)
        self.assertEqual(Comment.objects.count(), 2)
        self.assertIsNotNone(comment[0].deleted_at)


class PostReplyTestCase(TestCase):
    @classmethod
    def setUp(cls):
        cls.user1 = UserFactory(
            phone_number="01011112222",
            username="steve",
        )
        cls.user1_token = "JWT " + jwt_token_of(User.objects.get(phone_number="01011112222"))
        cls.user2 = UserFactory(phone_number="01022223333", username="mark")
        cls.user2_token = "JWT " + jwt_token_of(User.objects.get(phone_number="01022223333"))

        cls.location1 = LocationFactory(
            code="1111011700",
            place_name="서울특별시 종로구 당주동",
        )
        cls.user1.location = cls.location1
        cls.user1.save()

        cls.article1 = ArticleFactory(
            seller=cls.user1,
            location=cls.location1,
            price=3040000,
            title="맥북 판매",
            content="성능 좋은 맥북 판매해요.",
            category="디지털기기",
        )
        cls.comment1 = CommentFactory(
            commenter=cls.user2,
            article=cls.article1,
            content="맥북 구매 원합니다.",
            parent=None,
        )

        cls.article2 = ArticleFactory(
            seller=cls.user1,
            location=cls.location1,
            price=3040000,
            title="식물 판매",
            content="식물 팝니다.",
            category="식물",
        )
        cls.comment2 = CommentFactory(
            commenter=cls.user2,
            article=cls.article2,
            content="식물 구매 원합니다.",
            parent=None,
        )

        cls.post_data = {"content": "직거래 가능하신가요?"}

    def test_post_reply_no_login(self):
        a_id = str(self.article1.id)
        c_id = str(self.comment1.id)
        # no token
        data = self.post_data.copy()
        response = self.client.post("/api/v1/article/%s/comment/%s/" % (a_id, c_id), data=data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        self.assertEqual(Comment.objects.count(), 2)

    def test_post_reply_wrong_article_id(self):
        # wrong article id
        a_id = str(self.article1.id + 10)
        c_id = str(self.comment1.id)

        data = self.post_data.copy()
        response = self.client.post(
            "/api/v1/article/%s/comment/%s/" % (a_id, c_id), data=data, HTTP_AUTHORIZATION=self.user1_token
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        res_data = response.json()
        self.assertEqual(res_data[0], "해당하는 게시글을 찾을 수 없습니다.")

        self.assertEqual(Comment.objects.count(), 2)

    def test_post_reply_wrong_comment_id(self):
        a_id = str(self.article1.id)
        # wrong comment id
        c_id = str(self.comment1.id + 10)

        data = self.post_data.copy()
        response = self.client.post(
            "/api/v1/article/%s/comment/%s/" % (a_id, c_id), data=data, HTTP_AUTHORIZATION=self.user1_token
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        res_data = response.json()
        self.assertEqual(res_data[0], "해당하는 댓글을 찾을 수 없습니다.")

        self.assertEqual(Comment.objects.count(), 2)

    def test_post_reply_article_and_comment_unmatch(self):
        # article and comment do not match
        a_id = str(self.article1.id)
        c_id = str(self.comment2.id)

        data = self.post_data.copy()
        response = self.client.post(
            "/api/v1/article/%s/comment/%s/" % (a_id, c_id), data=data, HTTP_AUTHORIZATION=self.user1_token
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        res_data = response.json()
        self.assertEqual(res_data[0], "해당하는 댓글을 찾을 수 없습니다.")

        self.assertEqual(Comment.objects.count(), 2)

    def test_post_reply_wrong_information(self):
        a_id = str(self.article1.id)
        c_id = str(self.comment1.id)

        # no content
        response = self.client.post("/api/v1/article/%s/comment/%s/" % (a_id, c_id), data={}, HTTP_AUTHORIZATION=self.user1_token)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(Comment.objects.count(), 2)

        # invalid content
        response = self.client.post(
            "/api/v1/article/%s/comment/%s/" % (a_id, c_id), data={"content": "  "}, HTTP_AUTHORIZATION=self.user1_token
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(Comment.objects.count(), 2)

    def test_post_reply_sucess(self):
        a_id = str(self.article1.id)
        c_id = str(self.comment1.id)

        # successively add new reply
        data = self.post_data.copy()
        response = self.client.post(
            "/api/v1/article/%s/comment/%s/" % (a_id, c_id), data=data, HTTP_AUTHORIZATION=self.user1_token
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        res_data = response.data
        reply = res_data["comments"][0]["replies"][0]
        self.assertEqual(reply["id"], 3)
        self.assertEqual(reply["commenter"]["id"], self.user1.id)
        self.assertEqual(reply["content"], "직거래 가능하신가요?")
        self.assertIsNotNone(reply["created_at"])
        self.assertIsNone(reply["deleted_at"])
        self.assertEqual(reply["replies"], [])

        article = Article.objects.get(id=1)
        comment = Comment.objects.get(id=1)

        reply = Comment.objects.get(id=3)
        self.assertIsNotNone(comment.commenter)
        self.assertEqual(comment.article, article)
        self.assertEqual(reply.content, "직거래 가능하신가요?")
        self.assertEqual(reply.parent, comment)
        self.assertIsNotNone(comment.created_at)
        self.assertIsNone(comment.deleted_at)

        self.assertEqual(Comment.objects.count(), 3)
