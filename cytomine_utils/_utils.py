"""Utility functions used throughout the project."""

import typing as _tp
from pathlib import Path as _Path

import numpy as np

from cytomine import Cytomine as _Cytomine
from cytomine.models import (
    User,
    CurrentUser,
    Project,
    ProjectCollection,
    Storage,
    StorageCollection,
    ImageInstance,
    ImageInstanceCollection,
    Annotation,
    AnnotationCollection,
    AnnotationTerm,
    Ontology,
    OntologyCollection,
    Term,
    Property,
)

_GeoJSON = dict[str : str | _tp.Any]


def get_client() -> _Cytomine:
    """Get a Cytomine client."""
    keys = get_credentials()
    client = _Cytomine(**keys, verbose="INFO")
    return client


def connect() -> None:
    """Use a client to connect to Cytomine"""
    get_client()


def get_credentials(keys_file: _Path = None) -> dict[str, str]:
    """
    Retrieve credentials from a key file.

    Parameters
    ----------
    keys_file
        JSON file with credential information.
        Default is file present in `~/.cytomine.auth.json`.
    """
    import json

    if keys_file is None:
        keys_file = _Path("~/.cytomine.auth.json").expanduser()

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


def get_current_user() -> User:
    """Retrieve current user model."""
    return CurrentUser().fetch()


def get_user_by_id(id: int) -> User:
    """
    Retrieve user based on id.

    Parameters
    ----------
    id:
        ID of user.
    """
    return User(id=id).fetch()


def get_projects() -> list[Project]:
    """Retrieve all projects in Cytomine instance."""
    return ProjectCollection().fetch().data()


def get_project(name: str) -> Project:
    """
    Retrieve a project from a Cytomine instance based on its name.

    Parameters
    ----------
    name:
        Name of project to retrieve.
    """
    prjs = get_projects()
    return next(filter(lambda prj: prj.name == name, prjs)).fetch()


def get_storage() -> Storage:
    """Retrieve the user storage from a Cytomine instance."""
    storages = StorageCollection().fetch()
    me = get_current_user()
    return next(filter(lambda storage: storage.user == me.id, storages)).fetch()


def get_ontologies() -> list[Ontology]:
    """Retrieve ontologies across all projects."""
    return [x.fetch() for x in OntologyCollection().fetch()]


def get_images_of_project(
    project_name: str, **attributes: dict[str, _tp.Any]
) -> list[ImageInstance]:
    """
    Retrieve all images associated with a project.

    Parameters
    ----------
    project_name
        Name of project to retrieve images for.
    attributes
        Additional parameters are passed to :class:`ImageInstanceCollection`
        and can be used for additinoal filtering.
    """
    prj = get_project(project_name)
    img_col = ImageInstanceCollection(
        filters=dict(project=prj.id, **attributes)
    ).fetch()
    return img_col.data()


def get_all_images() -> list[ImageInstance]:
    """Retrieve all images across all projects."""
    prjs = get_projects()
    img_col = list()
    for prj in prjs:
        img_col += get_images_of_project(prj.name)
    return img_col


def get_image_by_name(image_name: str) -> ImageInstance:
    """
    Retrieve image based on its name.

    Parameters
    ---------
    image_name
        Name of the image to retrieve.
    """
    return next(
        filter(lambda x: x.filename.split("/")[-1] == image_name, get_all_images())
    )


def get_image_by_id(id: int) -> ImageInstance:
    """
    Retrieve image based on its ID.

    Parameters
    ---------
    id
        ID of the image to retrieve.
    """
    return ImageInstance(id=id).fetch()


def get_term_id_mapping() -> dict[str, id]:
    """
    Retrieve mapping of ontology terms and their IDs.
    Works across all ontologies.
    """
    mapping = dict()
    for ontology in get_ontologies():
        mapping |= {x["name"]: x["id"] for x in ontology.children}
    return mapping


def get_term_by_name(term_name: str) -> Term:
    """
    Retrieve ontology term based on its name.

    Parameters
    ---------
    term_name
        Name of the term to retrieve.
    """
    return get_term_by_id(get_term_id_mapping()[term_name])


def get_term_by_id(id: int) -> Term:
    """
    Retrieve term based on its ID.

    Parameters
    ---------
    id
        ID of the term to retrieve.
    """
    return Term(id=id).fetch()


def upload_image(
    image_file: _Path, project_name: str, **attributes: dict[str, str]
) -> None:
    """
    Upload image to Cytomine instance..

    Parameters
    ---------
    image_file
        Path to file to upload. Can be of several formats.
    project_name:
        Name of project to associate image with.
    attributes
        Additional attributes to add to the image.
    """
    prj = get_project(project_name)
    storage = get_storage()

    try:
        uploaded_file = client.upload_image(
            upload_host=keys["upload_host"],
            filename=image_file.as_posix(),
            id_storage=storage.id,
            id_project=prj.id,
            properties=attributes,
        )
    except TypeError:
        "'NoneType' object is not iterable"
        pass


def upload_annotations(
    geojson: _GeoJSON, project_name: str, image_file: str, dimensions: tuple[int, int]
) -> None:
    """
    Upload annotations of an image to Cytomine.

    Parameters
    ----------
    geojson
        Annotations to add in GeoJSON format.
    project_name
        Name of project to associate annotations with (should be the project of the image)
    image_file
        Image to associate annotations with.
    dimensions
        Shape of image.
    """
    from shapely.geometry import Polygon

    prj = get_project(project_name)
    imgs = get_images_of_project(prj.name)
    img = next(filter(lambda x: x.filename.split("/")[-1] == image_file, imgs))

    assert geojson["type"] == "FeatureCollection"

    for i, feature in enumerate(geojson["features"]):
        f = feature["geometry"]
        assert f["type"] in ["LineString", "Polygon"]
        coords = np.asarray(f["coordinates"])
        # Invert y axis
        coords = np.asarray([coords[:, 0], abs(coords[:, 1] - dimensions[1])]).T
        obj = Polygon(coords).buffer(0)
        if not obj.is_valid:
            print(f"Annotation number {i} is not valid!")
            continue

        annot = Annotation(location=obj.wkt, id_image=img.id, id_project=prj.id)
        annot.users = [get_current_user().id]
        annot.save()

        if "name" in feature["properties"]:
            term = AnnotationTerm(
                annot.id, get_term_by_name(feature["properties"]["name"].lower()).id
            )
            term.save()

        for k, v in feature["properties"].items():
            prop = Property(annot, key=k, value=v)
            prop.save()


def get_annotations_from_image(image_name: str) -> list[Annotation]:
    """
    Retrieve annotations from image.

    Parameters
    ----------
    image_name
        Name of image to retrieve annotations from.
    """
    img = get_image_by_name(image_name)
    annotations = AnnotationCollection(project=img.project, image=img.id).fetch()
    return [a.fetch() for a in annotations]


def get_annotations(project_name: str) -> list[Annotation]:
    """
    Retrieve annotations from all images in a project.

    Parameters
    ----------
    project_name
        Name of project to retrieve annotations from.
    """
    prj = get_project(project_name)
    annotations = AnnotationCollection(project=prj.id).fetch()
    annotations = [x.fetch() for x in annotations]
    return annotations


def backup_annotations(project_name: str, backup_json: _Path) -> None:
    """
    Retrieve annotations from project and save them to file.
    Right now it does not write in GeoJSON format.

    Parameters
    ----------
    project_name
        Name of project to retieve annotations from.
    backup_json
        Path to file to write annotations to.
    """
    # TODO: export as GeoJSON
    # backup_json = 'cytomine.annotations.backup.json'
    prj = get_project(project_name)
    annotations = AnnotationCollection(project=prj.id).fetch()

    annotations_wk = dict()
    for annot in annotations:
        annot.fetch()
        image_name = _Path(get_image_by_id(annot.image).filename).name
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
