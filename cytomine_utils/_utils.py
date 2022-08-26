"""Utility functions used throughout the project."""

import typing as tp

from pathlib import Path

from cytomine import Cytomine
from cytomine.models import (
    CurrentUser,
    StorageCollection,
    ImageInstance,
    ImageInstanceCollection,
    AnnotationCollection,
    Term,
    User,
)
from cytomine.models.project import ProjectCollection, Project
from cytomine.models.storage import Storage

__all__ = [
    "get_credentials",
    "get_projects",
    "get_project",
    "get_storage",
    "get_images_of_project",
    "get_image_by_id",
    "get_term_by_id",
    "get_user_by_id",
    "upload_tiff_to_cytomine",
    "backup_annotations",
    "update_image_with_attributes",
]


def get_credentials(keys_file: Path = None) -> dict[str, str]:
    import json

    if keys_file is None:
        keys_file = Path("~/.cytomine.auth.json").expanduser()

    if not keys_file.exists():
        raise FileNotFoundError(
            f"Cytomine file with credencials could not be found: '{keys_file}'"
        )
    with keys_file.open() as f:
        keys = json.load(f)
    # if "host" not in keys:
    #     keys["host"] = "cytomine.int.cemm.at"  # you can also use the IP: '10.110.81.123'
    # if "upload_host" not in keys:
    #     keys["upload_host"] = "cytomine-upload.int.cemm.at"
    return keys


def get_projects() -> list[Project]:
    return ProjectCollection().fetch().data()


def get_project(name: str) -> Project:
    prjs = get_projects()
    return next(filter(lambda prj: prj.name == name, prjs)).fetch()


def get_storage() -> Storage:
    storages = StorageCollection().fetch()
    me = CurrentUser().fetch()
    return next(filter(lambda storage: storage.user == me.id, storages)).fetch()


def get_images_of_project(project_name: str, **attributes) -> list[ImageInstance]:
    prj = get_project(project_name)
    img_col = ImageInstanceCollection(
        filters=dict(project=prj.id, **attributes)
    ).fetch()
    return img_col.data()


def get_image_by_id(id: int) -> ImageInstance:
    return ImageInstance(id=id).fetch()


def get_term_by_id(id: int) -> Term:
    return Term(id=id).fetch()


def get_user_by_id(id: int) -> User:
    return User(id=id).fetch()


def upload_tiff_to_cytomine(
    tiff_file: Path, project_name: str, **attributes: dict[str, str]
) -> None:

    prj = get_project(project_name)
    storage = get_storage()

    uploaded_file = client.upload_image(
        upload_host=keys["upload_host"],
        filename=tiff_file.as_posix(),
        id_storage=storage.id,
        id_project=prj.id,
        properties=attributes,
    )


def backup_annotations(project_name: str, backup_json: Path) -> None:
    # TODO: export as GeoJSON
    # backup_json = 'cytomine.annotations.backup.json'
    prj = get_project(project_name)
    annotations = AnnotationCollection(project=prj.id).fetch()

    annotations_wk = dict()
    for annot in annotations:
        annot.fetch()
        image_name = Path(get_image_by_id(annot.image).filename).name
        if image_name not in annotations_wk:
            annotations_wk[image_name] = list()

        # u = get_user_by_id(annot.user)
        annotations_wk[image_name].append(
            eval(annot.to_json().replace("false", "False"))
            # dict(
            #     terms=[get_term_by_id(x).name for x in annot.term],
            #     location=annot.location,
            #     created_time=annot.created,
            #     user=f"{u.firstname} {u.lastname}"
            # )
        )

    with open(backup_json, "w") as handle:
        json.dump(annotations_wk, handle, indent=4)


def update_image_with_attributes(
    tiff_file: Path, project_name: str, attributes: dict[str, str]
) -> None:
    keys = get_credentials()

    client = Cytomine(**keys, verbose="INFO")

    images = get_images_of_project(project_name)
    image = next(filter(lambda x: Path(x.filename).name == tiff_file.name, images))

    # Update
    ## Works
    image.resolution = 0.49
    image.magnification = 20
    ## Does not work
    image.populate(dict(data_type="he_wsi", project_name=project_name, **attributes))
    image.save()

    from cytomine.cytomine import Cytomine

    for attr in attributes:
        setattr(image, attr, attributes[attr])
    i = Cytomine.get_instance()
    i.put_model(image)

    resp = client._get(f"project.json", query_parameters={})
    resp = client._get(f"storage.json", query_parameters={})
    resp = client._get(f"abstractimage.json", query_parameters={})

    resp = client._post(f"abstractimage/{image.id}/histogram/extract.json")

    resp = client._get(
        f"imageinstance/{image.id}/sliceinstance.json", query_parameters=dict()
    )  # dict(max=0, offset=0)

    import requests
    from requests.auth import HTTPBasicAuth

    q = f"http://{keys['host']}/api/abstractimage/{image.id}/properties/populate.json"
    r = requests.post(
        q, data=attributes, auth=HTTPBasicAuth(keys["public_key"], keys["private_key"])
    )

    from cytomine.cytomine import CytomineAuth

    auth = CytomineAuth(keys["public_key"], keys["private_key"], keys["host"], "/api/")
    q = f"http://{keys['host']}/api/abstractimage/{image.id}.json"

    r = requests.put(q, data=attributes)
    auth(r)

    resp = client._put(f"abstractimage/{image.id}.json", query_parameters=attributes)


keys = get_credentials()
client = Cytomine(**keys, verbose="INFO")
